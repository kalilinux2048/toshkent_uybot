import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InputMediaPhoto

from config import BOT_TOKEN, ADMIN_IDS, REGIONS, CATEGORIES
from database import init_db, get_listings_by_region, get_listing_by_id, increment_views
from keyboards import get_regions_keyboard, get_categories_keyboard, get_listing_navigation_keyboard
from admin import admin_router
from collector import run_collector

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_web_server():
    PORT = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=PORT)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(admin_router)

# Foydalanuvchi uchun
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🏠 **Ko'chmas mulk botiga xush kelibsiz!**\n\n"
        "Viloyatni tanlang va e'lonlarni ko'ring:",
        reply_markup=get_regions_keyboard()
    )

@dp.callback_query(F.data.startswith("region_"))
async def select_region(call: types.CallbackQuery):
    await call.answer()
    region_key = call.data.replace("region_", "")
    region_name = REGIONS[region_key]
    
    await call.message.answer(
        f"📍 **{region_name}**\n\nKategoriya tanlang:",
        reply_markup=get_categories_keyboard(region_key)
    )

@dp.callback_query(F.data.startswith("category_"))
async def select_category(call: types.CallbackQuery):
    await call.answer()
    try:
        _, region_key, cat_key = call.data.split("_")
        region_name = REGIONS[region_key]
        category_name = CATEGORIES[cat_key]
        
        listings = await get_listings_by_region(region_key, category_name)
        
        if not listings:
            await call.message.answer(f"❌ {region_name} da {category_name} bo'yicha e'lon topilmadi!")
            return
        
        await show_listing(call.message, listings[0], region_key, cat_key, 0, len(listings))
        
    except Exception as e:
        print(f"Xatolik: {e}")
        await call.message.answer("❌ Xatolik yuz berdi!")

@dp.callback_query(F.data.startswith("nav_"))
async def navigate_listings(call: types.CallbackQuery):
    await call.answer()
    try:
        _, region_key, cat_key, index_str = call.data.split("_")
        current_index = int(index_str)
        category_name = CATEGORIES[cat_key]
        
        listings = await get_listings_by_region(region_key, category_name)
        
        if 0 <= current_index < len(listings):
            await show_listing(call.message, listings[current_index], region_key, cat_key, current_index, len(listings))
        else:
            await call.message.answer("❌ E'lon topilmadi!")
            
    except Exception as e:
        print(f"Xatolik: {e}")
        await call.message.answer("❌ Xatolik yuz berdi!")

async def show_listing(message, listing, region_key, cat_key, current_index, total_count):
    await increment_views(listing["id"])
    
    text = f"""
🏠 **{listing['title']}**

📍 **Manzil:** {listing['region_name']}
💰 **Narx:** {listing['price']} so'm
🛏 **Xonalar:** {listing['rooms']} xona
📞 **Telefon:** {listing['phone']}

📝 **Tavsif:**
{listing['description']}

👁 Ko'rishlar: {listing['views_count']}
🆔 ID: {listing['id']}
"""
    
    kb = get_listing_navigation_keyboard(region_key, cat_key, current_index, total_count)
    
    try:
        if listing.get('media_group') and len(listing['media_group']) > 1:
            media = []
            for i, photo_id in enumerate(listing['media_group']):
                if i == 0:
                    media.append(InputMediaPhoto(media=photo_id, caption=text))
                else:
                    media.append(InputMediaPhoto(media=photo_id))
            await message.answer_media_group(media=media)
            await message.answer("📌 Navigatsiya:", reply_markup=kb)
        elif listing.get('image_url'):
            await message.answer_photo(listing['image_url'], caption=text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)
    except Exception as e:
        print(f"Xatolik: {e}")
        await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_regions")
async def back_to_regions(call: types.CallbackQuery):
    await call.answer()
    await call.message.answer("📍 Viloyatni tanlang:", reply_markup=get_regions_keyboard())

@dp.message(Command("view"))
async def view_listing_by_id(message: types.Message):
    try:
        listing_id = int(message.text.split()[1])
        listing = await get_listing_by_id(listing_id)
        
        if not listing or listing['status'] != 'active':
            await message.answer("❌ Bunday ID bilan e'lon topilmadi!")
            return
        
        await increment_views(listing_id)
        
        text = f"""
🏠 **{listing['title']}**

📍 **Manzil:** {listing['region_name']}
💰 **Narx:** {listing['price']} so'm
🛏 **Xonalar:** {listing['rooms']} xona
📞 **Telefon:** {listing['phone']}

📝 **Tavsif:**
{listing['description']}

👁 Ko'rishlar: {listing['views_count']}
🆔 ID: {listing['id']}
"""
        
        if listing.get('media_group') and len(listing['media_group']) > 1:
            media = []
            for i, photo_id in enumerate(listing['media_group']):
                if i == 0:
                    media.append(InputMediaPhoto(media=photo_id, caption=text))
                else:
                    media.append(InputMediaPhoto(media=photo_id))
            await message.answer_media_group(media=media)
        elif listing.get('image_url'):
            await message.answer_photo(listing['image_url'], caption=text)
        else:
            await message.answer(text)
            
    except (IndexError, ValueError):
        await message.answer("❌ Format: /view 123")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

async def main():
    await init_db()
    print("✅ Bot ishga tushdi!")
    
    # Collector'ni alohida task'da ishga tushirish
    collector_task = asyncio.create_task(run_collector())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    asyncio.run(main())
