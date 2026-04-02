from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

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

def normalize_text(text):
    """Matnni normallashtirish"""
    if not text:
        return text
    return ' '.join(text.strip().split())

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

# STATISTIKA
@admin_router.callback_query(F.data == "admin_stats")
async def show_statistics(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    stats = await get_admin_statistics()
    
    regions_text = ""
    for reg in stats['regions']:
        reg_name = REGIONS.get(reg['region'], reg['region'])
        regions_text += f"• {reg_name}: {reg['count']} ta\n"
    
    districts_text = ""
    for dist in stats['districts']:
        districts_text += f"• {dist['district']}: {dist['count']} ta\n"
    
    categories_text = ""
    for cat in stats['categories']:
        cat_name = cat['category'].replace('🏠 ', '').replace('💰 ', '').replace('🏡 ', '')
        categories_text += f"• {cat_name}: {cat['count']} ta\n"
    
    top_text = ""
    for i, listing in enumerate(stats['top_listings'], 1):
        top_text += f"{i}. {listing['title'][:30]}... - {listing['views_count']} ko'rish\n"
    
    text = f"""
📊 **ADMIN STATISTIKA**

📌 **Umumiy ma'lumotlar:**
• Jami e'lonlar: {stats['total']} ta
• Faol e'lonlar: {stats['active']} ta
• Sotilgan: {stats['sold']} ta
• Ijaraga berilgan: {stats['rented']} ta
• Umumiy ko'rishlar: {stats['total_views']} ta
• Oxirgi 7 kunda: {stats['last_week']} ta

📍 **Viloyatlar bo'yicha:**
{regions_text if regions_text else '• Ma\'lumot yo\'q'}

📂 **Kategoriyalar:**
{categories_text}

🏘 **Eng faol tumanlar:**
{districts_text if districts_text else '• Ma\'lumot yo\'q'}

👁 **Eng ko'p ko'rilganlar:**
{top_text if top_text else '• Ma\'lumot yo\'q'}
    """
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Orqaga", callback_data="back_to_admin")
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

# O'CHIRISH MENYUSI
@admin_router.callback_query(F.data == "delete_listing_menu")
async def delete_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Admin panel", callback_data="back_to_admin")
    kb.adjust(1)
    await callback.message.edit_text(
        "❌ E'lonni o'chirish uchun e'lon ID sini yuboring.\n\n"
        "E'lon ID sini e'lon tagidagi '🆔 ID: ...' qatoridan topishingiz mumkin.\n\n"
        "Format: /delete 123",
        reply_markup=kb.as_markup()
    )

# O'CHIRISH KOMANDASI
@admin_router.message(Command("delete"))
async def delete_listing(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        listing_id = int(message.text.split()[1])
        listing = await get_listing_by_id(listing_id)
        
        if not listing:
            await message.answer("❌ Bunday ID bilan e'lon topilmadi!")
            return
        
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_{listing_id}")
        kb.button(text="❌ Yo'q, bekor qilish", callback_data="back_to_admin")
        kb.adjust(1)
        
        await message.answer(
            f"🔍 Topilgan e'lon:\n\n"
            f"🏠 {listing['title']}\n"
            f"📍 {listing['district']}\n"
            f"💰 {listing['price']}\n"
            f"📊 Holat: {listing['status']}\n\n"
            f"Rostdan ham o'chirilsinmi?",
            reply_markup=kb.as_markup()
        )
    except (IndexError, ValueError):
        await message.answer("❌ Noto'g'ri format. To'g'ri format: /delete 123")

# O'CHIRISHNI TASDIQLASH
@admin_router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    listing_id = int(callback.data.replace("confirm_delete_", ""))
    await delete_listing_by_id(listing_id)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Admin panel", callback_data="back_to_admin")
    kb.adjust(1)
    await callback.message.edit_text(
        f"✅ {listing_id} ID li e'lon muvaffaqiyatli o'chirildi!",
        reply_markup=kb.as_markup()
    )

# STATUS YANGILASH MENYUSI
@admin_router.callback_query(F.data == "update_status_menu")
async def update_status_menu(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Admin panel", callback_data="back_to_admin")
    kb.adjust(1)
    await callback.message.edit_text(
        "✅ E'lon holatini yangilash uchun ID va holatni yuboring.\n\n"
        "Formatlar:\n"
        "/sold 123 - Sotilgan deb belgilash\n"
        "/rented 123 - Ijaraga berilgan deb belgilash\n"
        "/active 123 - Qayta faollashtirish\n\n"
        "E'lon ID sini e'lon tagidagi '🆔 ID: ...' qatoridan topishingiz mumkin.",
        reply_markup=kb.as_markup()
    )

# SOTILGAN
@admin_router.message(Command("sold"))
async def mark_as_sold(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        listing_id = int(message.text.split()[1])
        listing = await get_listing_by_id(listing_id)
        
        if not listing:
            await message.answer("❌ Bunday ID bilan e'lon topilmadi!")
            return
        
        await update_listing_status(listing_id, 'sold')
        await message.answer(f"✅ {listing_id} ID li e'lon 'Sotilgan' deb belgilandi!")
    except (IndexError, ValueError):
        await message.answer("❌ Noto'g'ri format. To'g'ri format: /sold 123")

# IJARAGA BERILGAN
@admin_router.message(Command("rented"))
async def mark_as_rented(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        listing_id = int(message.text.split()[1])
        listing = await get_listing_by_id(listing_id)
        
        if not listing:
            await message.answer("❌ Bunday ID bilan e'lon topilmadi!")
            return
        
        await update_listing_status(listing_id, 'rented')
        await message.answer(f"✅ {listing_id} ID li e'lon 'Ijaraga berilgan' deb belgilandi!")
    except (IndexError, ValueError):
        await message.answer("❌ Noto'g'ri format. To'g'ri format: /rented 123")

# QAYTA FAOLLASHTIRISH
@admin_router.message(Command("active"))
async def mark_as_active(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        listing_id = int(message.text.split()[1])
        listing = await get_listing_by_id(listing_id)
        
        if not listing:
            await message.answer("❌ Bunday ID bilan e'lon topilmadi!")
            return
        
        await update_listing_status(listing_id, 'active')
        await message.answer(f"✅ {listing_id} ID li e'lon qayta faollashtirildi!")
    except (IndexError, ValueError):
        await message.answer("❌ Noto'g'ri format. To'g'ri format: /active 123")

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

# E'LON QO'SHISH - VILOYAT TANLASH
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

# VILOYAT TANLASH
@admin_router.callback_query(F.data.startswith("add_region_"))
async def add_select_region(callback: types.CallbackQuery, state: FSMContext):
    region_key = callback.data.replace("add_region_", "")
    await state.update_data(region=region_key)
    region_name = REGIONS[region_key]
    await callback.message.answer(f"✅ {region_name} tanlandi")
    
    kb = InlineKeyboardBuilder()
    if region_key in DISTRICTS:
        for d in DISTRICTS[region_key]:
            district_callback = d.replace(" ", "_")
            kb.button(text=d, callback_data=f"d_{district_callback}")
    kb.adjust(2)
    await callback.message.answer("📍 Tumanni tanlang:", reply_markup=kb.as_markup())
    await state.set_state(AddListingStates.district)

# TUMAN TANLASH
@admin_router.callback_query(F.data.startswith("d_"))
async def set_district(callback: types.CallbackQuery, state: FSMContext):
    district_callback = callback.data[2:]
    district = district_callback.replace("_", " ")
    district = normalize_text(district)
    await state.update_data(district=district)
    await callback.message.answer(f"✅ {district} tanlandi")

    kb = InlineKeyboardBuilder()
    for k, v in CATEGORIES.items():
        kb.button(text=v, callback_data=f"c_{k}")
    kb.adjust(1)
    await callback.message.answer("📂 Kategoriya:", reply_markup=kb.as_markup())
    await state.set_state(AddListingStates.category)

# KATEGORIYA TANLASH
@admin_router.callback_query(F.data.startswith("c_"))
async def set_category(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data[2:]
    category_name = CATEGORIES[key]
    await state.update_data(category=category_name)
    await callback.message.answer(f"✅ {category_name} tanlandi")
    await callback.message.answer("📝 Sarlavha yozing:")
    await state.set_state(AddListingStates.title)

# SARLAVHA
@admin_router.message(AddListingStates.title)
async def set_title(message: types.Message, state: FSMContext):
    await state.update_data(title=normalize_text(message.text))
    await message.answer("💰 Narx (so'mda):")
    await state.set_state(AddListingStates.price)

# NARX
@admin_router.message(AddListingStates.price)
async def set_price(message: types.Message, state: FSMContext):
    await state.update_data(price=normalize_text(message.text))
    await message.answer("🛏 Xonalar soni:")
    await state.set_state(AddListingStates.rooms)

# XONALAR SONI
@admin_router.message(AddListingStates.rooms)
async def set_rooms(message: types.Message, state: FSMContext):
    await state.update_data(rooms=normalize_text(message.text))
    await message.answer("📝 Tavsif yozing:")
    await state.set_state(AddListingStates.description)

# TAVSIF
@admin_router.message(AddListingStates.description)
async def set_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=normalize_text(message.text))
    await message.answer("📞 Telefon raqam:")
    await state.set_state(AddListingStates.phone)

# TELEFON
@admin_router.message(AddListingStates.phone)
async def set_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=normalize_text(message.text))
    await message.answer(
        "📸 **RASMLARNI YUBORING**\n\n"
        "Bir nechta rasm yuborishingiz mumkin.\n"
        "Har bir rasm uchun alohida yuboring.\n"
        "Barcha rasmlarni yuborib bo'lgach, **'done'** deb yozing.\n"
        "Agar rasm yo'q bo'lsa, **'skip'** deb yozing."
    )
    await state.update_data(images=[])
    await state.set_state(AddListingStates.images)

@admin_router.message(AddListingStates.images, F.photo)
async def add_image(message: types.Message, state: FSMContext):
    data = await state.get_data()
    images = data.get('images', [])
    
    photo_id = message.photo[-1].file_id
    images.append(photo_id)
    
    await state.update_data(images=images)
    await message.answer(
        f"✅ Rasm qo'shildi! Jami: {len(images)} ta rasm.\n"
        f"Yana rasm yuboring yoki tugatish uchun 'done' deb yozing."
    )

@admin_router.message(AddListingStates.images, F.text.lower() == "done")
async def finish_images(message: types.Message, state: FSMContext):
    data = await state.get_data()
    images = data.get('images', [])
    
    if not images:
        await message.answer("❌ Hech qanday rasm yubormadingiz. 'skip' deb yozib o'tkazib yuborishingiz mumkin.")
        return
    
    await message.answer(f"✅ {len(images)} ta rasm saqlandi. E'lon qo'shilmoqda...")
    await save_listing(message, state)

@admin_router.message(AddListingStates.images, F.text.lower() == "skip")
async def skip_images(message: types.Message, state: FSMContext):
    await state.update_data(images=[])
    await message.answer("✅ Rasmsiz e'lon qo'shilmoqda...")
    await save_listing(message, state)

@admin_router.message(AddListingStates.images)
async def invalid_input(message: types.Message, state: FSMContext):
    await message.answer(
        "❌ Noto'g'ri format. Iltimos, rasm yuboring yoki 'done' / 'skip' deb yozing."
    )

async def save_listing(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        
        required_fields = ['region', 'district', 'category', 'title', 'price', 'rooms', 'description', 'phone']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            await message.answer(f"❌ Xatolik: {missing_fields} maydonlari topilmadi. Qaytadan urinib ko'ring.")
            await state.clear()
            return
        
        images = data.get('images', [])
        
        # DEBUG: Saqlanayotgan ma'lumotlar
        print(f"DEBUG SAVE: Region: {data.get('region')}")
        print(f"DEBUG SAVE: District: '{data['district']}'")
        print(f"DEBUG SAVE: Category: {data['category']}")
        
        if images:
            listing_id = await add_listing(**data, media_group=images, image_url=images[0])
            await message.answer(f"✅ E'lon muvaffaqiyatli qo'shildi! ID: {listing_id}, {len(images)} ta rasm bilan.")
        else:
            listing_id = await add_listing(**data, image_url=None)
            await message.answer(f"✅ E'lon muvaffaqiyatli qo'shildi! ID: {listing_id} (rasmsiz)")
        
        await state.clear()
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()
        await message.answer(f"❌ Xatolik: {e}")
        await state.clear()
