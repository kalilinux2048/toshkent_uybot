from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import urllib.parse

from config import ADMIN_IDS, REGIONS, DISTRICTS, CATEGORIES
from database import add_listing, get_admin_statistics, update_listing_status, get_listing_by_id, delete_listing_by_id

admin_router = Router()

class AddListingStates(StatesGroup):
    region = State()
    district = State()
    category = State()
    title = State()
    price = State()
    rooms = State()
    description = State()
    phone = State()
    images = State()

# ADMIN PANEL
@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="➕ E'lon qo'shish", callback_data="add_listing")
    kb.button(text="📊 Statistika", callback_data="admin_stats")
    kb.button(text="❌ E'lonni o'chirish", callback_data="delete_listing_menu")
    kb.button(text="✅ Sotildi/Ijaraga berildi", callback_data="update_status_menu")
    kb.adjust(1)
    await message.answer("👨‍💼 Admin panel", reply_markup=kb.as_markup())

# ADMIN PANELGA QAYTISH
@admin_router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ E'lon qo'shish", callback_data="add_listing")
    kb.button(text="📊 Statistika", callback_data="admin_stats")
    kb.button(text="❌ E'lonni o'chirish", callback_data="delete_listing_menu")
    kb.button(text="✅ Sotildi/Ijaraga berildi", callback_data="update_status_menu")
    kb.adjust(1)
    await callback.message.edit_text("👨‍💼 Admin panel", reply_markup=kb.as_markup())

# ================== E'LON QO'SHISH ==================

@admin_router.callback_query(F.data == "add_listing")
async def start_add(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return

    kb = InlineKeyboardBuilder()
    for key, name in REGIONS.items():
        kb.button(text=name, callback_data=f"add_region_{key}")
    kb.adjust(2)

    await callback.message.answer("📍 Viloyatni tanlang:", reply_markup=kb.as_markup())
    await state.set_state(AddListingStates.region)

@admin_router.callback_query(F.data.startswith("add_region_"))
async def add_select_region(callback: types.CallbackQuery, state: FSMContext):
    region_key = callback.data.replace("add_region_", "")
    await state.update_data(region=region_key)

    kb = InlineKeyboardBuilder()
    for d in DISTRICTS.get(region_key, []):
        district_callback = urllib.parse.quote(d)
        kb.button(text=d, callback_data=f"d_{district_callback}")
    kb.adjust(2)

    await callback.message.answer("📍 Tumanni tanlang:", reply_markup=kb.as_markup())
    await state.set_state(AddListingStates.district)

@admin_router.callback_query(F.data.startswith("d_"))
async def set_district(callback: types.CallbackQuery, state: FSMContext):
    district_callback = callback.data[2:]
    district = urllib.parse.unquote(district_callback)

    await state.update_data(district=district)
    await callback.message.answer(f"✅ {district} tanlandi")

    kb = InlineKeyboardBuilder()
    for k, v in CATEGORIES.items():
        kb.button(text=v, callback_data=f"c_{k}")
    kb.adjust(1)

    await callback.message.answer("📂 Kategoriya:", reply_markup=kb.as_markup())
    await state.set_state(AddListingStates.category)

@admin_router.callback_query(F.data.startswith("c_"))
async def set_category(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data[2:]
    category_name = CATEGORIES[key]

    await state.update_data(category=category_name)
    await callback.message.answer(f"✅ {category_name} tanlandi")
    await callback.message.answer("📝 Sarlavha yozing:")
    await state.set_state(AddListingStates.title)

@admin_router.message(AddListingStates.title)
async def set_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("💰 Narx (so'mda):")
    await state.set_state(AddListingStates.price)

@admin_router.message(AddListingStates.price)
async def set_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("🛏 Xonalar soni:")
    await state.set_state(AddListingStates.rooms)

@admin_router.message(AddListingStates.rooms)
async def set_rooms(message: types.Message, state: FSMContext):
    await state.update_data(rooms=message.text)
    await message.answer("📝 Tavsif yozing:")
    await state.set_state(AddListingStates.description)

@admin_router.message(AddListingStates.description)
async def set_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("📞 Telefon raqam:")
    await state.set_state(AddListingStates.phone)

@admin_router.message(AddListingStates.phone)
async def set_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("📸 Rasmlarni yuboring (done / skip)")
    await state.update_data(images=[])
    await state.set_state(AddListingStates.images)

@admin_router.message(AddListingStates.images, F.photo)
async def add_image(message: types.Message, state: FSMContext):
    data = await state.get_data()
    images = data.get('images', [])

    images.append(message.photo[-1].file_id)
    await state.update_data(images=images)

    await message.answer(f"✅ {len(images)} ta rasm qo'shildi. Yana yuboring yoki done yozing")

@admin_router.message(AddListingStates.images, F.text.lower() == "done")
async def finish_images(message: types.Message, state: FSMContext):
    await save_listing(message, state)

@admin_router.message(AddListingStates.images, F.text.lower() == "skip")
async def skip_images(message: types.Message, state: FSMContext):
    await state.update_data(images=[])
    await save_listing(message, state)

async def save_listing(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()

        if data.get('images'):
            await add_listing(**data, media_group=data['images'], image_url=data['images'][0])
        else:
            await add_listing(**data, image_url=None)

        await message.answer("✅ E'lon qo'shildi!")
        await state.clear()

    except Exception as e:
        print(e)
        await message.answer("❌ Xatolik")
        await state.clear()
