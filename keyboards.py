from aiogram.utils.keyboard import InlineKeyboardBuilder
import urllib.parse
from config import REGIONS, DISTRICTS, CATEGORIES

def regions_keyboard():
    kb = InlineKeyboardBuilder()
    for key, name in REGIONS.items():
        kb.button(text=name, callback_data=f"reg_{key}")
    kb.adjust(2)
    return kb.as_markup()

def districts_keyboard(region_key):
    kb = InlineKeyboardBuilder()
    for d in DISTRICTS[region_key]:
        enc = urllib.parse.quote(d)
        kb.button(text=d, callback_data=f"dist_{region_key}_{enc}")
    kb.adjust(2)
    return kb.as_markup()

def categories_keyboard():
    kb = InlineKeyboardBuilder()
    for key, name in CATEGORIES.items():
        kb.button(text=name, callback_data=f"cat_{key}")
    kb.adjust(1)
    return kb.as_markup()
