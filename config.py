import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = "@toshkent_uybot"

ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip()]

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')

# VILOYATLAR
REGIONS = {
    "tashkent_city": "🏙 Toshkent shahri",
    "tashkent_region": "🏞 Toshkent viloyati",
    "andijan": "🏔 Andijon viloyati",
    "bukhara": "🕌 Buxoro viloyati",
    "jizzakh": "🏜 Jizzax viloyati",
    "qashqadaryo": "⛰ Qashqadaryo viloyati",
    "navoi": "🏜 Navoiy viloyati",
    "namangan": "🏞 Namangan viloyati",
    "samarkand": "🏛 Samarqand viloyati",
    "surkhandarya": "⛰ Surxondaryo viloyati",
    "sirdarya": "🏞 Sirdaryo viloyati",
    "fergana": "🌾 Farg'ona viloyati",
    "khorezm": "🏜 Xorazm viloyati",
    "karakalpakstan": "🏝 Qoraqalpog'iston Respublikasi"
}

CATEGORIES = {
    "rent": "🏠 Ijaraga beriladigan xonadonlar",
    "sale": "💰 Sotiladigan uylar",
    "subsidy": "🏡 Subsidiyaga beriladigan uylar"
}

# Har bir kanaldan saqlanadigan maksimal e'lonlar soni
MAX_LISTINGS_PER_CHANNEL = 10
