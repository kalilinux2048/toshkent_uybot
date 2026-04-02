import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InputMediaPhoto

from config import BOT_TOKEN, CATEGORIES, ADMIN_IDS, REGIONS, DISTRICTS
from database import init_db, get_all_listings, increment_views, get_listing_by_id, delete_listing_by_id, update_listing_status, get_all_listings_raw
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

def normalize_text(text):
    """Matnni normallashtirish"""
    if not text:
        return text
    return ' '.join(text.strip().split())

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🇺🇿 O'zbekiston Uy Bot\n\n"
        "🏘 Uy va xonadonlar qidirish uchun viloyatni tanlang:",
        reply_markup=get_regions_keyboard()
    )

@dp.message(Command("test"))
async def test_command(message: types.Message):
    """Test komandasi - bazadagi ma'lumotlarni tekshirish"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🚫 Ruxsat yo'q!")
        return
    
    # 1. Bazadagi barcha e'lonlarni ko'rsatish
    all_listings = await get_all_listings_raw()
    text = "📋 Bazadagi so'nggi 30 e'lon:\n\n"
    for l in all_listings:
        text += f"ID: {l['id']}, District: '{l['district']}', Category: {l['category'][:20]}, Status: {l['status']}\n"
    
    # 2. Toshkent shahri tumanlari uchun test
    test_districts = ["Bektemir tumani", "Chilonzor tumani", "Mirzo Ulug'bek tumani", "Yunusobod tumani"]
    text += "\n🔍 Qidiruv testi:\n"
    for td in test_districts:
        for cat_key, cat_name in CATEGORIES.items():
            count = len(await get_all_listings(td, cat_name))
            if count > 0:
                text += f"✅ {td} / {cat_name[:20]}: {count} ta\n"
    
    text += "\n💡 Agar hech nima ko'rinmasa, yangi e'lon qo'shib ko'ring."
    
    # Xabarni bo'lib yuborish (agar uzun bo'lsa)
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i+4000])
    else:
        await message.answer(text)

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
        district = normalize_text(district)
        
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
        
        # DEBUG: Barcha qismlarni chiqarish
        print(f"DEBUG: Full callback data: {data}")
        print(f"DEBUG: Parts: {parts}")
        
        region_key = parts[1]
        cat_key = parts[-1]
        
        # district_parts ni to'g'ri aniqlash (2-indexdan oxirgidan oldingigacha)
        district_parts = parts[2:-1]
        district_callback = "_".join(district_parts)
        district = district_callback.replace("_", " ")
        district = normalize_text(district)
        
        cat_name = CATEGORIES[cat_key]

        print(f"DEBUG: region_key = '{region_key}'")
        print(f"DEBUG: cat_key = '{cat_key}'")
        print(f"DEBUG: district = '{district}'")
        print(f"DEBUG: cat_name = '{cat_name}'")
        
        listings = await get_all_listings(district, cat_name)
        
        print(f"DEBUG: {len(listings)} ta e'lon topildi")
        
        total_count = len(listings)

        if total_count == 0:
            await call.message.answer(f"❌ {district} tumanida {cat_name} bo'yicha e'lon topilmadi\n\n💡 Yangi e'lon qo'shish uchun /admin buyrug'idan foydalaning.")
            return

        await show_listing(
            call.message, listings[0], region_key, district_callback, cat_key, 0, total_count
        )
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()
        await call.message.answer(f"❌ Xatolik yuz berdi: {str(e)[:100]}")

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
        district = normalize_text(district)
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
            media = []
            for i, photo_id in enumerate(listing['media_group']):
                if i == 0:
                    media.append(InputMediaPhoto(media=photo_id, caption=text))
                else:
                    media.append(InputMediaPhoto(media=photo_id))
            
            await message.answer_media_group(media=media)
            await message.answer("📌 Amallar:", reply_markup=final_kb)
            
        elif listing.get('image_url'):
            await message.answer_photo(
                listing['image_url'], 
                caption=text, 
                reply_markup=final_kb
            )
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
            media = []
            for i, photo_id in enumerate(listing['media_group']):
                if i == 0:
                    media.append(InputMediaPhoto(media=photo_id, caption=text))
                else:
                    media.append(InputMediaPhoto(media=photo_id))
            
            await message.answer_media_group(media=media)
            if kb:
                await message.answer("📌 Amallar:", reply_markup=kb)
                
        elif listing.get('image_url'):
            await message.answer_photo(listing['image_url'], caption=text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)
            
    except (IndexError, ValueError):
        await message.answer("❌ Noto'g'ri format. To'g'ri format: /view 123")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

# ADMIN TEZKOR TUGMALAR
@dp.callback_query(F.data.startswith("admin_delete_"))
async def admin_quick_delete(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Ruxsat yo'q!")
        return
    
    listing_id = int(callback.data.replace("admin_delete_", ""))
    await delete_listing_by_id(listing_id)
    await callback.answer("✅ E'lon o'chirildi!")
    await callback.message.delete()

@dp.callback_query(F.data.startswith("admin_sold_"))
async def admin_quick_sold(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Ruxsat yo'q!")
        return
    
    listing_id = int(callback.data.replace("admin_sold_", ""))
    await update_listing_status(listing_id, 'sold')
    await callback.answer("✅ Sotilgan deb belgilandi!")
    
    if callback.message.caption:
        new_text = callback.message.caption + "\n\n✅ HOLAT: SOTILGAN"
        await callback.message.edit_caption(caption=new_text)

@dp.callback_query(F.data.startswith("admin_rented_"))
async def admin_quick_rented(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Ruxsat yo'q!")
        return
    
    listing_id = int(callback.data.replace("admin_rented_", ""))
    await update_listing_status(listing_id, 'rented')
    await callback.answer("✅ Ijaraga berilgan deb belgilandi!")
    
    if callback.message.caption:
        new_text = callback.message.caption + "\n\n✅ HOLAT: IJARAGA BERILGAN"
        await callback.message.edit_caption(caption=new_text)

async def main():
    await init_db()
    print("✅ Bot ishga tushdi!")
    print("📝 Admin komandalari: /admin, /test")
    await dp.start_polling(bot)

if __name__ == "__main__":
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    asyncio.run(main())
