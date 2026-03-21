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

async def add_listing(**kwargs):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
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
            kwargs['district'],
            kwargs['category'],
            kwargs['title'],
            kwargs['price'],
            kwargs['rooms'],
            kwargs['description'],
            kwargs['phone'],
            image_url,
            media_group_json
        )
        
        await conn.close()
        return result['id']
        
    except Exception as e:
        await conn.close()
        print(f"❌ add_listing xatolik: {e}")
        raise e

async def get_all_listings(district, category):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    rows = await conn.fetch("""
    SELECT * FROM listings
    WHERE district = $1 AND category = $2 AND status = 'active'
    ORDER BY id DESC
    """, district, category)
    
    await conn.close()
    
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
