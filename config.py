import os
from dotenv import load_dotenv

# .env faylidan ma'lumotlarni yuklash
load_dotenv()

# BOT_TOKEN endi .env dan olinadi
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = "@toshkent_uybot"

# ADMIN_IDS ham .env dan olinadi
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip()]

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

# TUMANLAR
DISTRICTS = {
    "tashkent_city": [
        "Bektemir tumani", "Chilonzor tumani", "Hamza tumani", "Mirobod tumani",
        "Mirzo Ulug'bek tumani", "Olmazor tumani", "Sergeli tumani",
        "Shayxontohur tumani", "Uchtepa tumani", "Yakkasaroy tumani",
        "Yashnobod tumani", "Yunusobod tumani"
    ],
    "tashkent_region": [
        "Nurafshon shahri", "Olmaliq shahri", "Angren shahri", "Bekobod shahri",
        "Bo'ka tumani", "Bo'stonliq tumani", "Chinoz tumani", "Qibray tumani",
        "Ohangaron tumani", "Oqqo'rg'on tumani", "Parkent tumani", "Piskent tumani",
        "Quyi Chirchiq tumani", "Toshkent tumani", "O'rta Chirchiq tumani",
        "Yuqori Chirchiq tumani", "Zangiota tumani", "Yangiyo'l tumani"
    ],
    "sirdarya": [
        "Guliston shahri", "Yangiyer shahri", "Shirin shahri", "Boyovut tumani",
        "Guliston tumani", "Xovos tumani", "Mirzaobod tumani", "Oqoltin tumani",
        "Sardoba tumani", "Sayxunobod tumani", "Sirdaryo tumani"
    ],
    "andijan": [
        "Andijon shahri", "Xonobod shahri", "Andijon tumani", "Asaka tumani",
        "Baliqchi tumani", "Buloqboshi tumani", "Bo'ston tumani", "Jalaquduq tumani",
        "Izboskan tumani", "Qo'rg'ontepa tumani", "Marhamat tumani", "Oltinko'l tumani",
        "Paxtaobod tumani", "Ulug'nor tumani", "Xo'jaobod tumani", "Shahrixon tumani"
    ],
    "bukhara": [
        "Buxoro shahri", "Kogon shahri", "Buxoro tumani", "Vobkent tumani",
        "G'ijduvon tumani", "Jondor tumani", "Kogon tumani", "Qorako'l tumani",
        "Qorovulbozor tumani", "Olot tumani", "Peshku tumani", "Romitan tumani",
        "Shofirkon tumani"
    ],
    "jizzakh": [
        "Jizzax shahri", "Arnasoy tumani", "Baxmal tumani", "Do'stlik tumani",
        "Forish tumani", "G'allaorol tumani", "Sharof Rashidov tumani",
        "Mirzacho'l tumani", "Paxtakor tumani", "Yangiobod tumani", "Zomin tumani",
        "Zafarobod tumani", "Zarbdor tumani"
    ],
    "qashqadaryo": [
        "Qarshi shahri", "Shahrisabz shahri", "Dehqonobod tumani", "Kasbi tumani",
        "Kitob tumani", "Koson tumani", "Mirishkor tumani", "Muborak tumani",
        "Nishon tumani", "Chiroqchi tumani", "Shahrisabz tumani", "Yakkabog' tumani",
        "G'uzor tumani", "Qamashi tumani", "Qarshi tumani"
    ],
    "navoi": [
        "Navoiy shahri", "Zarafshon shahri", "Karmana tumani", "Konimex tumani",
        "Navbahor tumani", "Nurota tumani", "Qiziltepa tumani", "Tomdi tumani",
        "Uchquduq tumani", "Xatirchi tumani"
    ],
    "namangan": [
        "Namangan shahri", "Chortoq tumani", "Chust tumani", "Kosonsoy tumani",
        "Mingbuloq tumani", "Namangan tumani", "Norin tumani", "Pop tumani",
        "To'raqo'rg'on tumani", "Uychi tumani", "Uchqo'rg'on tumani", "Yangiqo'rg'on tumani"
    ],
    "samarkand": [
        "Samarqand shahri", "Bulung'ur tumani", "Ishtixon tumani", "Jomboy tumani",
        "Kattaqo'rg'on shahri", "Qo'shrabot tumani", "Narpay tumani", "Nurobod tumani",
        "Oqdaryo tumani", "Payariq tumani", "Pastdarg'om tumani", "Paxtachi tumani",
        "Samarqand tumani", "Toyloq tumani", "Urgut tumani"
    ],
    "surkhandarya": [
        "Termiz shahri", "Boysun tumani", "Denov tumani", "Jarqo'rg'on tumani",
        "Muzrabot tumani", "Oltinsoy tumani", "Sariosiyo tumani", "Sherobod tumani",
        "Sho'rchi tumani", "Termiz tumani", "Uzun tumani", "Qiziriq tumani",
        "Qumqo'rg'on tumani", "Angor tumani", "Bandixon tumani"
    ],
    "fergana": [
        "Farg'ona shahri", "Qo'qon shahri", "Marg'ilon shahri", "Quvasoy shahri",
        "Beshariq tumani", "Bog'dod tumani", "Buvayda tumani", "Dang'ara tumani",
        "Yozyovon tumani", "Oltiariq tumani", "Qo'shtepa tumani", "Rishton tumani",
        "So'x tumani", "Toshloq tumani", "Uchko'prik tumani", "Farg'ona tumani",
        "Furqat tumani"
    ],
    "khorezm": [
        "Urganch shahri", "Xiva shahri", "Bog'ot tumani", "Gurlan tumani",
        "Qo'shko'pir tumani", "Xazorasp tumani", "Xiva tumani", "Shovot tumani",
        "Tuproqqal'a tumani", "Urganch tumani", "Yangiariq tumani", "Yangibozor tumani"
    ],
    "karakalpakstan": [
        "Nukus shahri", "Amudaryo tumani", "Beruniy tumani", "Bo'zatov tumani",
        "Kegayli tumani", "Qorao'zak tumani", "Qonliko'l tumani", "Qo'ng'irot tumani",
        "Mo'ynoq tumani", "Nukus tumani", "Taxtako'pir tumani", "To'rtko'l tumani",
        "Xo'jayli tumani", "Chimboy tumani", "Shumanoy tumani", "Ellikqal'a tumani"
    ]
}

# KATEGORIYALAR
CATEGORIES = {
    "rent": "🏠 Ijaraga beriladigan xonadonlar",
    "sale": "💰 Sotiladigan uylar",
    "subsidy": "🏡 Subsidiyaga beriladigan uylar"
}
