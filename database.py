import aiosqlite
from datetime import datetime, timedelta
import json

DB_NAME = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        
        try:
            await db.execute("ALTER TABLE listings ADD COLUMN media_group TEXT")
        except:
            pass
        
        print("✅ Ma'lumotlar bazasi tayyor")

async def add_listing(**kwargs):
    async with aiosqlite.connect(DB_NAME) as db:
        print("=" * 50)
        print("📝 E'lon qo'shilmoqda:")
        for key, value in kwargs.items():
            print(f"   {key}: {value}")
        print("=" * 50)
        
        try:
            if 'media_group' in kwargs and kwargs['media_group']:
                media_group_json = json.dumps(kwargs['media_group'])
                image_url = kwargs.get('media_group', [None])[0]
            else:
                media_group_json = None
                image_url = kwargs.get('image_url', None)
            
            await db.execute("""
            INSERT INTO listings (
                region, district, category, title, price, rooms, 
                description, phone, image_url, media_group, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
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
            ))
            await db.commit()
            
            cursor = await db.execute("SELECT last_insert_rowid()")
            last_id = await cursor.fetchone()
            print(f"✅ E'lon bazaga qo'shildi! ID: {last_id[0]}")
            
            return last_id[0]
        except Exception as e:
            print(f"❌ Xatolik: {e}")
            raise e

async def get_all_listings(district, category):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
        SELECT * FROM listings
        WHERE district = ? AND category = ? AND status = 'active'
        ORDER BY id DESC
        """, (district, category))
        return await cursor.fetchall()

async def increment_views(listing_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE listings SET views_count = views_count + 1 WHERE id = ?", (listing_id,))
        await db.commit()

async def delete_listing_by_id(listing_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
        await db.commit()

async def get_listing_by_id(listing_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM listings WHERE id=?", (listing_id,))
        row = await cursor.fetchone()
        
        if row and row['media_group']:
            media_group = json.loads(row['media_group'])
            row_dict = dict(row)
            row_dict['media_group'] = media_group
            return row_dict
        
        return row

async def get_admin_statistics():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute("SELECT COUNT(*) as total FROM listings")
        total_listings = (await cursor.fetchone())['total']
        
        cursor = await db.execute("SELECT COUNT(*) as total FROM listings WHERE status='active'")
        active_listings = (await cursor.fetchone())['total']
        
        cursor = await db.execute("SELECT COUNT(*) as total FROM listings WHERE status='sold'")
        sold_listings = (await cursor.fetchone())['total']
        
        cursor = await db.execute("SELECT COUNT(*) as total FROM listings WHERE status='rented'")
        rented_listings = (await cursor.fetchone())['total']
        
        cursor = await db.execute("SELECT SUM(views_count) as total FROM listings")
        total_views = (await cursor.fetchone())['total'] or 0
        
        cursor = await db.execute("""
            SELECT category, COUNT(*) as count 
            FROM listings WHERE status='active'
            GROUP BY category
        """)
        categories = await cursor.fetchall()
        
        cursor = await db.execute("""
            SELECT region, COUNT(*) as count 
            FROM listings WHERE status='active'
            GROUP BY region ORDER BY count DESC LIMIT 5
        """)
        regions = await cursor.fetchall()
        
        cursor = await db.execute("""
            SELECT district, COUNT(*) as count 
            FROM listings WHERE status='active'
            GROUP BY district ORDER BY count DESC LIMIT 5
        """)
        districts = await cursor.fetchall()
        
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        cursor = await db.execute("SELECT COUNT(*) as count FROM listings WHERE created_at > ?", (week_ago,))
        last_week = (await cursor.fetchone())['count']
        
        cursor = await db.execute("SELECT title, views_count FROM listings ORDER BY views_count DESC LIMIT 5")
        top_listings = await cursor.fetchall()
        
        return {
            'total': total_listings,
            'active': active_listings,
            'sold': sold_listings,
            'rented': rented_listings,
            'total_views': total_views,
            'categories': categories,
            'regions': regions,
            'districts': districts,
            'last_week': last_week,
            'top_listings': top_listings
        }

async def update_listing_status(listing_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE listings SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, listing_id))
        await db.commit()
