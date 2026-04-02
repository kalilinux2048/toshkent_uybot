import asyncpg
import json
import os
from datetime import datetime, timedelta

async def init_db():
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL topilmadi! PostgreSQL yaratganmisiz?")
            return False
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id SERIAL PRIMARY KEY,
            region TEXT,
            district TEXT,
            category TEXT,
            title TEXT,
            price TEXT,
            rooms TEXT,
            description TEXT,
            phone TEXT,
            image_url TEXT,
            media_group TEXT,
            views_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        await conn.close()
        print("✅ PostgreSQL bazasi tayyor")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL xatolik: {e}")
        return False

def normalize_text(text):
    """Matnni normallashtirish - probellarni tozalash"""
    if not text:
        return text
    # Bir nechta probellarni bitta probelga aylantirish
    return ' '.join(text.strip().split())

async def add_listing(**kwargs):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Tuman nomini normallashtirish
        district = normalize_text(kwargs['district'])
        title = normalize_text(kwargs['title'])
        description = normalize_text(kwargs['description'])
        phone = normalize_text(kwargs['phone'])
        price = normalize_text(kwargs['price'])
        rooms = normalize_text(kwargs['rooms'])
        
        if 'media_group' in kwargs and kwargs['media_group']:
            media_group_json = json.dumps(kwargs['media_group'])
            image_url = kwargs['media_group'][0]
        else:
            media_group_json = None
            image_url = kwargs.get('image_url')
        
        result = await conn.fetchrow("""
        INSERT INTO listings (
            region, district, category, title, price, rooms, 
            description, phone, image_url, media_group, status
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'active')
        RETURNING id
        """, 
            kwargs.get('region', 'tashkent_city'),
            district,
            kwargs['category'],
            title,
            price,
            rooms,
            description,
            phone,
            image_url,
            media_group_json
        )
        
        await conn.close()
        print(f"✅ E'lon qo'shildi: ID={result['id']}, District='{district}'")
        return result['id']
        
    except Exception as e:
        await conn.close()
        print(f"❌ add_listing xatolik: {e}")
        raise e

async def get_all_listings_raw():
    """Barcha e'lonlarni statusdan qat'iy nazar olish (debug uchun)"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    rows = await conn.fetch("""
    SELECT id, district, category, status, title, region 
    FROM listings 
    ORDER BY id DESC
    LIMIT 30
    """)
    
    await conn.close()
    
    result = []
    for row in rows:
        result.append(dict(row))
    
    return result

async def get_all_listings(district, category):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Normallashtirish
    district_norm = normalize_text(district)
    
    # DEBUG: Bazadagi barcha tumanlarni ko'rish
    all_districts = await conn.fetch("SELECT DISTINCT district, status FROM listings WHERE category = $1", category)
    print(f"DEBUG: Bazadagi '{category}' kategoriyasidagi tumanlar:")
    for d in all_districts:
        print(f"  - '{d['district']}' (status: {d['status']})")
    
    print(f"DEBUG: Qidirilayotgan district: '{district_norm}'")
    
    # Katta-kichik harf sezgirligini yo'qotish va normallashtirish
    rows = await conn.fetch("""
    SELECT * FROM listings
    WHERE LOWER(REPLACE(district, '  ', ' ')) = LOWER($1) 
    AND category = $2 
    AND status = 'active'
    ORDER BY id DESC
    """, district_norm, category)
    
    await conn.close()
    
    print(f"DEBUG: Qidiruv natijasi: {len(rows)} ta active e'lon")
    
    # Agar 0 ta bo'lsa, statusi active bo'lmaganlarini tekshirish
    if len(rows) == 0:
        conn2 = await asyncpg.connect(DATABASE_URL)
        inactive = await conn2.fetch("""
        SELECT id, status, district FROM listings
        WHERE LOWER(REPLACE(district, '  ', ' ')) = LOWER($1) AND category = $2
        """, district_norm, category)
        await conn2.close()
        if inactive:
            print(f"DEBUG: {len(inactive)} ta e'lon bor lekin statusi active emas:")
            for i in inactive:
                print(f"  - ID: {i['id']}, status: {i['status']}, district: '{i['district']}'")
    
    result = []
    for row in rows:
        row_dict = dict(row)
        if row_dict.get('media_group'):
            try:
                row_dict['media_group'] = json.loads(row_dict['media_group'])
            except:
                row_dict['media_group'] = None
        result.append(row_dict)
    
    return result

async def increment_views(listing_id):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("UPDATE listings SET views_count = views_count + 1 WHERE id = $1", listing_id)
    await conn.close()

async def delete_listing_by_id(listing_id):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("DELETE FROM listings WHERE id = $1", listing_id)
    await conn.close()
    print(f"✅ E'lon o'chirildi: ID={listing_id}")

async def get_listing_by_id(listing_id):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT * FROM listings WHERE id = $1", listing_id)
    await conn.close()
    
    if row:
        row_dict = dict(row)
        if row_dict.get('media_group'):
            try:
                row_dict['media_group'] = json.loads(row_dict['media_group'])
            except:
                row_dict['media_group'] = None
        return row_dict
    return None

async def get_admin_statistics():
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    total = await conn.fetchval("SELECT COUNT(*) FROM listings")
    active = await conn.fetchval("SELECT COUNT(*) FROM listings WHERE status='active'")
    sold = await conn.fetchval("SELECT COUNT(*) FROM listings WHERE status='sold'")
    rented = await conn.fetchval("SELECT COUNT(*) FROM listings WHERE status='rented'")
    total_views = await conn.fetchval("SELECT COALESCE(SUM(views_count), 0) FROM listings")
    
    categories = await conn.fetch("SELECT category, COUNT(*) FROM listings WHERE status='active' GROUP BY category")
    regions = await conn.fetch("SELECT region, COUNT(*) FROM listings WHERE status='active' GROUP BY region ORDER BY count DESC LIMIT 5")
    districts = await conn.fetch("SELECT district, COUNT(*) FROM listings WHERE status='active' GROUP BY district ORDER BY count DESC LIMIT 5")
    
    week_ago = datetime.now() - timedelta(days=7)
    last_week = await conn.fetchval("SELECT COUNT(*) FROM listings WHERE created_at > $1", week_ago)
    top_listings = await conn.fetch("SELECT title, views_count FROM listings ORDER BY views_count DESC LIMIT 5")
    
    await conn.close()
    
    return {
        'total': total, 'active': active, 'sold': sold, 'rented': rented,
        'total_views': total_views, 'categories': categories, 'regions': regions,
        'districts': districts, 'last_week': last_week, 'top_listings': top_listings
    }

async def update_listing_status(listing_id, status):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("UPDATE listings SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2", status, listing_id)
    await conn.close()
    print(f"✅ E'lon holati yangilandi: ID={listing_id}, status={status}")
