from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import REGIONS, CATEGORIES

def get_regions_keyboard():
    kb = InlineKeyboardBuilder()
    for key, name in REGIONS.items():
        kb.button(text=name, callback_data=f"region_{key}")
    kb.adjust(2)
    return kb.as_markup()

def get_categories_keyboard(region_key):
    kb = InlineKeyboardBuilder()
    for key, val in CATEGORIES.items():
        kb.button(text=val, callback_data=f"category_{region_key}_{key}")
    kb.adjust(1)
    return kb.as_markup()

def get_listing_navigation_keyboard(region_key, category_key, current_index, total_count):
    kb = InlineKeyboardBuilder()
    
    if current_index > 0:
        kb.button(text="⬅️ Oldingi", callback_data=f"nav_{region_key}_{category_key}_{current_index-1}")
    
    kb.button(text=f"📊 {current_index+1}/{total_count}", callback_data="none")
    
    if current_index < total_count - 1:
        kb.button(text="Keyingi ➡️", callback_data=f"nav_{region_key}_{category_key}_{current_index+1}")
    
    kb.button(text="🔙 Viloyatlar", callback_data="back_to_regions")
    kb.adjust(3, 1)
    return kb.as_markup()

def get_admin_channels_keyboard(region_key, region_name):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Kanal qo'shish", callback_data=f"add_channel_{region_key}")
    kb.button(text="❌ Kanal o'chirish", callback_data=f"remove_channel_{region_key}")
    kb.button(text="📋 Kanallar ro'yxati", callback_data=f"list_channels_{region_key}")
    kb.button(text="🔙 Orqaga", callback_data="back_to_admin")
    kb.adjust(1)
    return kb.as_markup()
