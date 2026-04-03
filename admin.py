from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS, REGIONS, CATEGORIES
from database import (
    get_listings_by_region, get_listing_by_id, delete_listing_by_id,
    add_channel_binding, remove_channel_binding, get_channels_by_region,
    get_admin_statistics, increment_views
)
from keyboards import get_regions_keyboard, get_categories_keyboard, get_listing_navigation_keyboard, get_admin_channels_keyboard
from collector import collector

admin_router = Router()

class AddChannelStates(StatesGroup):
    waiting_for_channel = State()

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="admin_stats")
    kb.button(text="🔗 Kanal biriktirish", callback_data="bind_channel_menu")
    kb.button(text="📋 E'lonlar", callback_data="listings_menu")
    kb.adjust(1)
    await message.answer("👨‍💼 Admin panel", reply_markup=kb.as_markup())

@admin_router.callback_query(F.data == "admin_stats")
async def show_statistics(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    stats = await get_admin_statistics()
    
    text = f"""
📊 **ADMIN STATISTIKA**

📌 **Umumiy ma'lumotlar:**
• Jami e'lonlar: {stats['total']} ta
• Biriktirilgan kanallar: {stats['total_channels']} ta
• Umumiy ko'rishlar: {stats['total_views']} ta

📍 **Viloyatlar bo'yicha:**
"""
    for reg in stats['region_stats']:
        text += f"• {reg['region_name']}: {reg['count']} ta\n"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Orqaga", callback_data="back_to_admin")
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

@admin_router.callback_query(F.data == "bind_channel_menu")
async def bind_channel_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    kb = InlineKeyboardBuilder()
    for key, name in REGIONS.items():
        kb.button(text=name, callback_data=f"bind_region_{key}")
    kb.button(text="🔙 Orqaga", callback_data="back_to_admin")
    kb.adjust(2)
    await callback.message.edit_text("📍 Qaysi viloyatga kanal biriktirmoqchisiz?", reply_markup=kb.as_markup())

@admin_router.callback_query(F.data.startswith("bind_region_"))
async def select_region_for_bind(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    region_key = callback.data.replace("bind_region_", "")
    region_name = REGIONS[region_key]
    
    await state.update_data(region_key=region_key, region_name=region_name)
    await state.set_state(AddChannelStates.waiting_for_channel)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Bekor qilish", callback_data="bind_channel_menu")
    
    await callback.message.edit_text(
        f"📢 **{region_name}** uchun kanal yoki guruhni biriktiring.\n\n"
        f"Kanal username sini yoki ID sini yuboring:\n"
        f"Masalan: @reklama_kanali yoki -1001234567890\n\n"
        f"⚠️ Bot (user account) shu kanalda a'zo bo'lishi kerak!",
        reply_markup=kb.as_markup()
    )

@admin_router.message(AddChannelStates.waiting_for_channel)
async def add_channel(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    data = await state.get_data()
    region_key = data.get('region_key')
    region_name = data.get('region_name')
    channel_input = message.text.strip()
    
    try:
        # Kanalga ulanish
        from collector import collector
        entity = await collector.client.get_entity(channel_input)
        
        channel_id = str(entity.id)
        channel_title = entity.title
        channel_username = entity.username or ""
        
        # Bazaga saqlash
        await add_channel_binding(region_key, region_name, channel_id, channel_title, channel_username)
        
        # Shu kanaldan e'lonlarni darhol sinxronizatsiya qilish
        from collector import collector
        channel_info = {
            'region_key': region_key,
            'region_name': region_name,
            'channel_id': channel_id,
            'channel_title': channel_title
        }
        await collector.sync_channel_messages(channel_info)
        
        await message.answer(f"✅ **{channel_title}** kanali **{region_name}** ga biriktirildi!\n\n📥 Oxirgi e'lonlar sinxronizatsiya qilindi.")
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)[:200]}\n\nIltimos, to'g'ri kanal username yoki ID sini yuboring.")

@admin_router.callback_query(F.data.startswith("remove_channel_"))
async def remove_channel_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    region_key = callback.data.replace("remove_channel_", "")
    region_name = REGIONS[region_key]
    
    channels = await get_channels_by_region(region_key)
    
    if not channels:
        await callback.answer(f"❌ {region_name} ga hech qanday kanal biriktirilmagan!")
        return
    
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.button(text=f"❌ {ch['channel_title']}", callback_data=f"del_channel_{ch['channel_id']}")
    kb.button(text="🔙 Orqaga", callback_data="bind_channel_menu")
    kb.adjust(1)
    
    await callback.message.edit_text(f"🗑 **{region_name}** dan qaysi kanalni o'chirmoqchisiz?", reply_markup=kb.as_markup())

@admin_router.callback_query(F.data.startswith("del_channel_"))
async def confirm_remove_channel(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    channel_id = callback.data.replace("del_channel_", "")
    
    await remove_channel_binding(channel_id)
    
    await callback.answer("✅ Kanal o'chirildi!")
    await callback.message.edit_text("✅ Kanal muvaffaqiyatli o'chirildi!")
    
    await asyncio.sleep(2)
    await bind_channel_menu(callback)

@admin_router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="admin_stats")
    kb.button(text="🔗 Kanal biriktirish", callback_data="bind_channel_menu")
    kb.button(text="📋 E'lonlar", callback_data="listings_menu")
    kb.adjust(1)
    await callback.message.edit_text("👨‍💼 Admin panel", reply_markup=kb.as_markup())
