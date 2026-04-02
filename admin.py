from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import urllib.parse

from config import ADMIN_IDS, REGIONS, DISTRICTS, CATEGORIES
from database import add_listing

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

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="➕ E'lon qo'shish", callback_data="add")
    kb.adjust(1)
    await message.answer("Admin panel", reply_markup=kb.as_markup())

@admin_router.callback_query(F.data == "add")
async def start_add(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for k, v in REGIONS.items():
        kb.button(text=v, callback_data=f"reg_{k}")
    kb.adjust(2)

    await callback.message.answer("Viloyat:", reply_markup=kb.as_markup())
    await state.set_state(AddListingStates.region)

@admin_router.callback_query(F.data.startswith("reg_"))
async def set_region(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.replace("reg_", "")
    await state.update_data(region=key)

    kb = InlineKeyboardBuilder()
    for d in DISTRICTS[key]:
        enc = urllib.parse.quote(d)
        kb.button(text=d, callback_data=f"dist_{enc}")
    kb.adjust(2)

    await callback.message.answer("Tuman:", reply_markup=kb.as_markup())
    await state.set_state(AddListingStates.district)

@admin_router.callback_query(F.data.startswith("dist_"))
async def set_district(callback: types.CallbackQuery, state: FSMContext):
    enc = callback.data.replace("dist_", "")
    district = urllib.parse.unquote(enc)

    await state.update_data(district=district)

    kb = InlineKeyboardBuilder()
    for k, v in CATEGORIES.items():
        kb.button(text=v, callback_data=f"cat_{k}")
    kb.adjust(1)

    await callback.message.answer("Kategoriya:", reply_markup=kb.as_markup())
    await state.set_state(AddListingStates.category)

@admin_router.callback_query(F.data.startswith("cat_"))
async def set_cat(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.replace("cat_", "")
    await state.update_data(category=CATEGORIES[key])
    await callback.message.answer("Sarlavha:")
    await state.set_state(AddListingStates.title)

@admin_router.message(AddListingStates.title)
async def title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Narx:")
    await state.set_state(AddListingStates.price)

@admin_router.message(AddListingStates.price)
async def price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Xonalar:")
    await state.set_state(AddListingStates.rooms)

@admin_router.message(AddListingStates.rooms)
async def rooms(message: types.Message, state: FSMContext):
    await state.update_data(rooms=message.text)
    await message.answer("Tavsif:")
    await state.set_state(AddListingStates.description)

@admin_router.message(AddListingStates.description)
async def desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Telefon:")
    await state.set_state(AddListingStates.phone)

@admin_router.message(AddListingStates.phone)
async def phone(message: types.Message, state: FSMContext):
    data = await state.get_data()

    await add_listing(
        region=data['region'],
        district=data['district'],
        category=data['category'],
        title=data['title'],
        price=data['price'],
        rooms=data['rooms'],
        description=data['description'],
        phone=message.text
    )

    await message.answer("SAQLANDI ✅")
    await state.clear()
