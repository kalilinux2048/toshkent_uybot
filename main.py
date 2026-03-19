import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InputMediaPhoto  # O'ZGARTIRILDI: MediaGroup o'rniga

from config import BOT_TOKEN, CATEGORIES, ADMIN_IDS, REGIONS
from database import init_db, get_all_listings, increment_views, get_listing_by_id
from keyboards import (
    get_regions_keyboard,
    get_districts_keyboard,
    get_categories_keyboard,
    get_listing_navigation_keyboard
)
from admin import admin_router

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

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🇺🇿 O'zbekiston Uy Bot\n\n"
        "🏘 Uy va xonadonlar qidirish uchun viloyatni tanlang:",
        reply_markup=get_regions_keyboard()
    )

@dp.callback_query(F.data.startswith("region_"))
async def select_region(call: types.CallbackQuery):
    await call.answer()
    region_key = call.data.replace("region_", "")
    region_name = REGIONS[region_key]
    await call.message.answer(
        f"📍 {region_name} - tumanni tanlang:",
        reply_markup=get_districts_keyboard(region_key)
    )

@dp.callback_query(F.data.startswith("district_"))
async def select_district(call: types.CallbackQuery):
    await call.answer()
    try:
        data = call.data
        parts = data.split("_")
        region_key = parts[1]
        district_parts = parts[2:]
        district_callback = "_".join(district_parts)
        district = district_callback.replace("_", " ")
        
        await call.message.answer(
            f"✅ {district} tanlandi\n\n📂 Kategoriya tanlang:",
            reply_markup=get_categories_keyboard(region_key, district_callback)
        )
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        await call.message.answer("❌ Xatolik yuz berdi")

@dp.callback_query(F.data.startswith("category_"))
async def select_category(call: types.CallbackQuery):
    await call.answer()
    try:
        data = call.data
        parts = data.split("_")
        region_key = parts[1]
        cat_key = parts[-1]
        district_parts = parts[2:-1]
        district_callback = "_".join(district_parts)
        district = district_callback.replace("_", " ")
        cat_name = CATEGORIES[cat_key]

        listings = await get_all_listings(district, cat_name)
        total_count = len(listings)

        if total_count == 0:
            await call.message.answer(f"❌ {district} tumanida {cat_name} bo'yicha e'lon topilmadi")
            return

        await show_listing(
            call.message, listings[0], region_key, district_callback, cat_key, 0, total_count
        )
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        await call.message.answer("❌ Xatolik yuz berdi")

@dp.callback_query(F.data == "back_to_regions")
async def back_to_regions(call: types.CallbackQuery):
    await call.answer()
    await call.message.answer("🇺🇿 Viloyatni tanlang:", reply_markup=get_regions_keyboard())

@dp.callback_query(F.data.startswith("nav_"))
async def navigate_listings(call: types.CallbackQuery):
    await call.answer()
    try:
        data = call.data
        parts = data.split("_")
        region_key = parts[1]
        cat_key = parts[-2]
        new_index = int(parts[-1])
        district_parts = parts[2:-2]
        district_callback = "_".join(district_parts)
        district = district_callback.replace("_", " ")
        cat_name = CATEGORIES[cat_key]

        listings = await get_all_listings(district, cat_name)
        total_count = len(listings)

        if 0 <= new_index < total_count:
            await show_listing(
                call.message, listings[new_index], region_key, district_callback, cat_key, new_index, total_count
            )
        else:
            await call.message.answer("❌ E'lon topilmadi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        await call.message.answer("❌ Xatolik yuz berdi")

async def show_listing(message, listing, region_key, district_callback, cat_key, current_index, total_count):
    await increment_views(listing["id"])
    
    text = (
        f"🏠 {listing['title']}\n"
        f"📍 {listing['district']}\n"
        f"💰 {listing['price']} so'm\n"
        f"🛏 {listing['rooms']} xona\n"
        f"📝 {listing['description']}\n"
        f"📞 {listing['phone']}\n"
        f"👁 Ko'rishlar: {listing['views_count']}\n"
        f"🆔 ID: {listing['id']}\n"
        f"📊 {current_index+1}/{total_count} e'lon"
    )
    
    nav_kb = get_listing_navigation_keyboard(region_key, district_callback, cat_key, current_index, total_count)
    
    if message.chat.id in ADMIN_IDS:
        admin_kb = InlineKeyboardBuilder()
        admin_kb.button(text="❌ O'chirish", callback_data=f"admin_delete_{listing['id']}")
        admin_kb.button(text="✅ Sotildi", callback_data=f"admin_sold_{listing['id']}")
        admin_kb.button(text="🏠 Ijaraga berildi", callback_data=f"admin_rented_{listing['id']}")
        admin_kb.adjust(1)
        
        combined_kb = InlineKeyboardBuilder()
        if nav_kb and hasattr(nav_kb, 'inline_keyboard'):
            for row in nav_kb.inline_keyboard:
                for button in row:
                    combined_kb.button(text=button.text, callback_data=button.callback_data)
        if admin_kb and hasattr(admin_kb, 'inline_keyboard'):
            for row in admin_kb.inline_keyboard:
                for button in row:
                    combined_kb.button(text=button.text, callback_data=button.callback_data)
        combined_kb.adjust(1)
        final_kb = combined_kb.as_markup()
    else:
        final_kb = nav_kb
    
    try:
        if listing.get('media_group') and len(listing['media_group']) > 1:
            # O'ZGARTIRILDI: MediaGroup o'rniga InputMediaPhoto ishlatish
            media = []
            for i, photo_id in enumerate(listing['media_group']):
                if i == 0:
                    media.append(InputMediaPhoto(media=photo_id, caption=text))
                else:
                    media.append(InputMediaPhoto(media=photo_id))
            await message.answer_media_group(media=media)
            await message.answer("Amallar:", reply_markup=final_kb)
        elif listing.get('image_url'):
            await message.answer_photo(listing['image_url'], caption=text, reply_markup=final_kb)
        else:
            await message.answer(text, reply_markup=final_kb)
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        await message.answer(text, reply_markup=final_kb)

@dp.message(Command("view"))
async def view_listing_by_id(message: types.Message):
    try:
        listing_id = int(message.text.split()[1])
        listing = await get_listing_by_id(listing_id)
        
        if not listing:
            await message.answer("❌ Bunday ID bilan e'lon topilmadi!")
            return
        
        await increment_views(listing_id)
        
        text = (
            f"🏠 {listing['title']}\n"
            f"📍 {listing['district']}\n"
            f"💰 {listing['price']} so'm\n"
            f"🛏 {listing['rooms']} xona\n"
            f"📝 {listing['description']}\n"
            f"📞 {listing['phone']}\n"
            f"📊 Holat: {listing['status']}\n"
            f"👁 Ko'rishlar: {listing['views_count']}\n"
            f"🆔 ID: {listing['id']}"
        )
        
        kb = None
        if message.from_user.id in ADMIN_IDS:
            admin_kb = InlineKeyboardBuilder()
            admin_kb.button(text="❌ O'chirish", callback_data=f"admin_delete_{listing_id}")
            admin_kb.button(text="✅ Sotildi", callback_data=f"admin_sold_{listing_id}")
            admin_kb.button(text="🏠 Ijaraga berildi", callback_data=f"admin_rented_{listing_id}")
            admin_kb.adjust(1)
            kb = admin_kb.as_markup()
        
        if listing.get('media_group') and len(listing['media_group']) > 1:
            # O'ZGARTIRILDI: MediaGroup o'rniga InputMediaPhoto ishlatish
            media = []
            for i, photo_id in enumerate(listing['media_group']):
                if i == 0:
                    media.append(InputMediaPhoto(media=photo_id, caption=text))
                else:
                    media.append(InputMediaPhoto(media=photo_id))
            await message.answer_media_group(media=media)
            if kb:
                await message.answer("Amallar:", reply_markup=kb)
        elif listing.get('image_url'):
            await message.answer_photo(listing['image_url'], caption=text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@dp.callback_query(F.data.startswith("admin_delete_"))
async def admin_quick_delete(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Ruxsat yo'q!")
        return
    
    listing_id = int(callback.data.replace("admin_delete_", ""))
    from database import delete_listing_by_id
    await delete_listing_by_id(listing_id)
    await callback.answer("✅ O'chirildi!")
    await callback.message.delete()

@dp.callback_query(F.data.startswith("admin_sold_"))
async def admin_quick_sold(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Ruxsat yo'q!")
        return
    
    listing_id = int(callback.data.replace("admin_sold_", ""))
    from database import update_listing_status
    await update_listing_status(listing_id, 'sold')
    await callback.answer("✅ Sotilgan deb belgilandi!")

@dp.callback_query(F.data.startswith("admin_rented_"))
async def admin_quick_rented(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Ruxsat yo'q!")
        return
    
    listing_id = int(callback.data.replace("admin_rented_", ""))
    from database import update_listing_status
    await update_listing_status(listing_id, 'rented')
    await callback.answer("✅ Ijaraga berilgan deb belgilandi!")

async def main():
    await init_db()
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    asyncio.run(main())
