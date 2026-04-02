import asyncio
import os
import urllib.parse

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InputMediaPhoto

from config import BOT_TOKEN, CATEGORIES, ADMIN_IDS, REGIONS
from database import init_db, get_all_listings, increment_views, get_listing_by_id, delete_listing_by_id, update_listing_status
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
        parts = call.data.split("_")
        region_key = parts[1]
        district_callback = "_".join(parts[2:])
        district = urllib.parse.unquote(district_callback)

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
        parts = call.data.split("_")
        region_key = parts[1]
        cat_key = parts[-1]
        district_callback = "_".join(parts[2:-1])
        district = urllib.parse.unquote(district_callback)
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
        parts = call.data.split("_")
        region_key = parts[1]
        cat_key = parts[-2]
        new_index = int(parts[-1])
        district_callback = "_".join(parts[2:-2])
        district = urllib.parse.unquote(district_callback)
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

    try:
        if listing.get('media_group') and len(listing['media_group']) > 1:
            media = []
            for i, photo_id in enumerate(listing['media_group']):
                if i == 0:
                    media.append(InputMediaPhoto(media=photo_id, caption=text))
                else:
                    media.append(InputMediaPhoto(media=photo_id))

            await message.answer_media_group(media=media)
            await message.answer("📌 Amallar:", reply_markup=nav_kb)

        elif listing.get('image_url'):
            await message.answer_photo(
                listing['image_url'],
                caption=text,
                reply_markup=nav_kb
            )
        else:
            await message.answer(text, reply_markup=nav_kb)

    except Exception as e:
        print(f"❌ Xatolik: {e}")
        await message.answer(text, reply_markup=nav_kb)

async def main():
    await init_db()
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    asyncio.run(main())
