import sqlite3

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
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
        status TEXT DEFAULT 'active'
    )
    """)
    conn.commit()
    conn.close()

def add_listing(region, district, category, title, price, rooms, description, phone, image_url=None, media_group=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    media_str = ",".join(media_group) if media_group else ""
    cursor.execute("""
    INSERT INTO listings (region, district, category, title, price, rooms, description, phone, image_url, media_group)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (region, district, category, title, price, rooms, description, phone, image_url, media_str))
    conn.commit()
    conn.close()

def get_all_listings(district="", category=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM listings WHERE district LIKE ? AND category LIKE ? AND status='active'
    """, (f"%{district}%", f"%{category}%"))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "region": row[1],
            "district": row[2],
            "category": row[3],
            "title": row[4],
            "price": row[5],
            "rooms": row[6],
            "description": row[7],
            "phone": row[8],
            "image_url": row[9],
            "media_group": row[10].split(",") if row[10] else [],
            "views_count": row[11],
            "status": row[12]
        })
    return result

def get_listing_by_id(listing_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM listings WHERE id=?", (listing_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "region": row[1],
        "district": row[2],
        "category": row[3],
        "title": row[4],
        "price": row[5],
        "rooms": row[6],
        "description": row[7],
        "phone": row[8],
        "image_url": row[9],
        "media_group": row[10].split(",") if row[10] else [],
        "views_count": row[11],
        "status": row[12]
    }

def update_listing_status(listing_id, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE listings SET status=? WHERE id=?", (status, listing_id))
    conn.commit()
    conn.close()

def delete_listing_by_id(listing_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM listings WHERE id=?", (listing_id,))
    conn.commit()
    conn.close()

def increment_views(listing_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE listings SET views_count = views_count + 1 WHERE id=?", (listing_id,))
    conn.commit()
    conn.close()
