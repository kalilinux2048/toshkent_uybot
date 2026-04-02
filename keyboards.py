from aiogram.utils.keyboard import InlineKeyboardBuilder
import urllib.parse
from config import REGIONS, DISTRICTS, CATEGORIES

def get_regions_keyboard():
    kb = InlineKeyboardBuilder()
    for key, name in REGIONS.items():
        kb.button(text=name, callback_data=f"region_{key}")
    kb.adjust(2)
    return kb.as_markup()

def get_districts_keyboard(region_key):
    kb = InlineKeyboardBuilder()
    for d in DISTRICTS[region_key]:
        encoded = urllib.parse.quote(d)
        kb.button(text=d, callback_data=f"district_{region_key}_{encoded}")
    kb.adjust(2)
    return kb.as_markup()

def get_categories_keyboard(region_key, district_callback):
    kb = InlineKeyboardBuilder()
    for key, name in CATEGORIES.items():
        kb.button(text=name, callback_data=f"category_{region_key}_{district_callback}_{key}")
    kb.adjust(1)
    return kb.as_markup()

def get_listing_navigation_keyboard(region, district, cat, index, total):
    kb = InlineKeyboardBuilder()

    if index > 0:
        kb.button(text="⬅️", callback_data=f"nav_{region}_{district}_{cat}_{index-1}")
    if index < total - 1:
        kb.button(text="➡️", callback_data=f"nav_{region}_{district}_{cat}_{index+1}")

    kb.adjust(2)
    return kb.as_markup()
