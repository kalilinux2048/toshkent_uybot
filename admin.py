from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import urllib.parse

from config import ADMIN_IDS, REGIONS, DISTRICTS, CATEGORIES
from database import add_listing, get_listing_by_id, update_listing_status, delete_listing_by_id

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
    kb.button(text="➕ E'lon qo'shish", callback_data="add_listing")
    kb.button(text="❌ E'lon o'chirish", callback_data="delete_listing_menu")
    kb.button(text="✅ Holat yangilash", callback_data="update_status_menu")
    kb.adjust(1)
    await message.answer("Admin panel", reply_markup=kb.as_markup())
