from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import REGIONS, DISTRICTS, CATEGORIES

# VILOYATLAR TUGMALARI
def get_regions_keyboard():
    kb = InlineKeyboardBuilder()
    for key, name in REGIONS.items():
        kb.button(text=name, callback_data=f"region_{key}")
    kb.adjust(2)
    return kb.as_markup()

# TUMANLAR TUGMALARI
def get_districts_keyboard(region_key):
    kb = InlineKeyboardBuilder()
    if region_key in DISTRICTS:
        for district in DISTRICTS[region_key]:
            # Tumanni _ bilan bog'lab yuboramiz
            district_callback = district.replace(" ", "_")
            kb.button(text=district, callback_data=f"district_{region_key}_{district_callback}")
    kb.adjust(2)
    return kb.as_markup()

# KATEGORIYA TUGMALARI
def get_categories_keyboard(region_key, district_callback):
    kb = InlineKeyboardBuilder()
    for key, val in CATEGORIES.items():
        kb.button(text=val, callback_data=f"category_{region_key}_{district_callback}_{key}")
    kb.adjust(1)
    return kb.as_markup()

# E'LONLARNI SAHIFALASH
def get_listing_navigation_keyboard(region_key, district_callback, cat_key, current_index, total_count):
    kb = InlineKeyboardBuilder()
    
    if current_index > 0:
        kb.button(
            text="⬅️ Oldingi e'lon", 
            callback_data=f"nav_{region_key}_{district_callback}_{cat_key}_{current_index-1}"
        )
    
    if current_index < total_count - 1:
        kb.button(
            text="Keyingi e'lon ➡️", 
            callback_data=f"nav_{region_key}_{district_callback}_{cat_key}_{current_index+1}"
        )
    
    kb.button(text="🔙 Viloyatlar", callback_data="back_to_regions")
    kb.adjust(1)
    return kb.as_markup()