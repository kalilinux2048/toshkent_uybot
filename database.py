import asyncpg
import json
import os
from datetime import datetime, timedelta

async def init_db():
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL topilmadi!")
            return False
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Asosiy e'lonlar jadvali
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id SERIAL PRIMARY KEY,
            region_key TEXT,
            region_name TEXT,
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
            source_chat_id TEXT,
            source_chat_title TEXT,
            source_message_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Kanal biriktirish jadvali (bir viloyatga ko'p kanal)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS channel_bindings (
            id SERIAL PRIMARY KEY,
            region_key TEXT,
            region_name TEXT,
            channel_id TEXT,
            channel_title TEXT,
            channel_username TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            last_sync TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        await conn.close()
        print("✅ PostgreSQL bazasi tayyor")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL xatolik: {e}")
        return False

# ============ E'LONLAR BILAN ISHLASH ============

async def add_or_update_listing(region_key, region_name, category, source_chat_id, source_chat_title, source_message_id, **kwargs):
    """E'lon qo'shish yoki yangilash"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Avval shu xabar saqlanganmi tekshirish
        existing = await conn.fetchrow("""
        SELECT id FROM listings WHERE source_chat_id = $1 AND source_message_id = $2
        """, str(source_chat_id), str(source_message_id))
        
        if existing:
            # Yangilash
            await conn.execute("""
            UPDATE listings SET 
                title = $1, price = $2, rooms = $3, description = $4, phone = $5,
                image_url = $6, media_group = $7, updated_at = CURRENT_TIMESTAMP
            WHERE source_chat_id = $8 AND source_message_id = $9
            """,
                kwargs.get('title', 'E\'lon')[:200],
                kwargs.get('price', 'Narxi aniqlanmadi'),
                kwargs.get('rooms', '?'),
                kwargs.get('description', '')[:1000],
                kwargs.get('phone', 'Raqam topilmadi'),
                kwargs.get('image_url'),
                kwargs.get('media_group'),
                str(source_chat_id),
                str(source_message_id)
            )
            return existing['id']
        else:
            # Yangi qo'shish
            result = await conn.fetchrow("""
            INSERT INTO listings (
                region_key, region_name, category, title, price, rooms, 
                description, phone, image_url, media_group, status,
                source_chat_id, source_chat_title, source_message_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'active', $11, $12, $13)
            RETURNING id
            """, 
                region_key,
                region_name,
                category,
                kwargs.get('title', 'E\'lon')[:200],
                kwargs.get('price', 'Narxi aniqlanmadi'),
                kwargs.get('rooms', '?'),
                kwargs.get('description', '')[:1000],
                kwargs.get('phone', 'Raqam topilmadi'),
                kwargs.get('image_url'),
                kwargs.get('media_group'),
                str(source_chat_id),
                source_chat_title,
                str(source_message_id)
            )
            
            # Har bir kanalda MAX_LISTINGS_PER_CHANNEL dan ortiq bo'lsa, eskilarni o'chirish
            await cleanup_old_listings(conn, source_chat_id)
            
            return result['id']
        
    except Exception as e:
        await conn.close()
        raise e
    finally:
        await conn.close()


async def cleanup_old_listings(conn, source_chat_id):
    """Bir kanaldagi eski e'lonlarni tozalash (faqat oxirgi 10 tasi qolsin)"""
    from config import MAX_LISTINGS_PER_CHANNEL
    
    # Shu kanaldagi e'lonlarni vaqt bo'yicha tartiblash
    rows = await conn.fetch("""
    SELECT id FROM listings 
    WHERE source_chat_id = $1 AND status = 'active'
    ORDER BY created_at DESC
    """, str(source_chat_id))
    
    # Agar 10 tadan ko'p bo'lsa, qolganlarini o'chirish
    if len(rows) > MAX_LISTINGS_PER_CHANNEL:
        to_delete = rows[MAX_LISTINGS_PER_CHANNEL:]
        for row in to_delete:
            await conn.execute("UPDATE listings SET status = 'deleted' WHERE id = $1", row['id'])
        print(f"🗑 {len(to_delete)} ta eski e'lon o'chirildi (kanal: {source_chat_id})")


async def get_listings_by_region(region_key, category, limit=50):
    """Viloyat bo'yicha faol e'lonlarni olish (eng yangilari birinchi)"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    rows = await conn.fetch("""
    SELECT * FROM listings
    WHERE region_key = $1 AND category = $2 AND status = 'active'
    ORDER BY created_at DESC
    LIMIT $3
    """, region_key, category, limit)
    
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


async def delete_listing_by_id(listing_id):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("UPDATE listings SET status = 'deleted' WHERE id = $1", listing_id)
    await conn.close()


async def delete_listing_by_source(source_chat_id, source_message_id):
    """Manba bo'yicha e'lonni o'chirish"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
    UPDATE listings SET status = 'deleted' 
    WHERE source_chat_id = $1 AND source_message_id = $2
    """, str(source_chat_id), str(source_message_id))
    await conn.close()


async def increment_views(listing_id):
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("UPDATE listings SET views_count = views_count + 1 WHERE id = $1", listing_id)
    await conn.close()


# ============ KANAL BIRIKTIRISH ============

async def add_channel_binding(region_key, region_name, channel_id, channel_title, channel_username=""):
    """Kanalni viloyatga biriktirish"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Avval shu kanal biriktirilganmi tekshirish
    existing = await conn.fetchrow("""
    SELECT id FROM channel_bindings WHERE channel_id = $1
    """, str(channel_id))
    
    if existing:
        await conn.execute("""
        UPDATE channel_bindings SET 
            region_key = $1, region_name = $2, channel_title = $3, 
            channel_username = $4, is_active = TRUE, updated_at = CURRENT_TIMESTAMP
        WHERE channel_id = $5
        """, region_key, region_name, channel_title, channel_username, str(channel_id))
    else:
        await conn.execute("""
        INSERT INTO channel_bindings (region_key, region_name, channel_id, channel_title, channel_username)
        VALUES ($1, $2, $3, $4, $5)
        """, region_key, region_name, str(channel_id), channel_title, channel_username)
    
    await conn.close()


async def remove_channel_binding(channel_id):
    """Kanal biriktirishni o'chirish"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    await conn.execute("""
    UPDATE channel_bindings SET is_active = FALSE WHERE channel_id = $1
    """, str(channel_id))
    
    # Shu kanaldagi barcha e'lonlarni ham o'chirish
    await conn.execute("""
    UPDATE listings SET status = 'deleted' WHERE source_chat_id = $1
    """, str(channel_id))
    
    await conn.close()


async def get_channels_by_region(region_key):
    """Viloyatga biriktirilgan barcha faol kanallarni olish"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    rows = await conn.fetch("""
    SELECT * FROM channel_bindings 
    WHERE region_key = $1 AND is_active = TRUE
    ORDER BY created_at DESC
    """, region_key)
    
    await conn.close()
    return [dict(row) for row in rows]


async def get_all_active_channels():
    """Barcha faol kanallarni olish"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    rows = await conn.fetch("""
    SELECT * FROM channel_bindings WHERE is_active = TRUE
    """)
    
    await conn.close()
    return [dict(row) for row in rows]


async def update_channel_sync_time(channel_id):
    """Kanalning oxirgi sinxronizatsiya vaqtini yangilash"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    await conn.execute("""
    UPDATE channel_bindings SET last_sync = CURRENT_TIMESTAMP WHERE channel_id = $1
    """, str(channel_id))
    
    await conn.close()


async def get_admin_statistics():
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = await asyncpg.connect(DATABASE_URL)
    
    total = await conn.fetchval("SELECT COUNT(*) FROM listings WHERE status = 'active'")
    total_channels = await conn.fetchval("SELECT COUNT(*) FROM channel_bindings WHERE is_active = TRUE")
    total_views = await conn.fetchval("SELECT COALESCE(SUM(views_count), 0) FROM listings WHERE status = 'active'")
    
    # Viloyatlar bo'yicha statistika
    region_stats = await conn.fetch("""
    SELECT region_name, COUNT(*) as count 
    FROM listings 
    WHERE status = 'active' 
    GROUP BY region_name 
    ORDER BY count DESC
    """)
    
    await conn.close()
    
    return {
        'total': total,
        'total_channels': total_channels,
        'total_views': total_views,
        'region_stats': [dict(r) for r in region_stats]
    }
