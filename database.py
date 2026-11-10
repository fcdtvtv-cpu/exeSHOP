import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                product TEXT,
                name TEXT,
                contact TEXT,
                task TEXT,
                status TEXT DEFAULT 'new',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                user_id INTEGER,
                name TEXT,
                product TEXT,
                rating INTEGER,
                text TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def create_order(user_id, username, product, name, contact, task):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO orders (user_id, username, product, name, contact, task) VALUES (?,?,?,?,?,?)",
            (user_id, username, product, name, contact, task),
        )
        await db.commit()
        return cur.lastrowid

async def get_order(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        return await cur.fetchone()

async def mark_paid(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status='paid' WHERE id=?", (order_id,))
        await db.commit()

async def save_review(order_id, user_id, name, product, rating, text):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reviews (order_id, user_id, name, product, rating, text) VALUES (?,?,?,?,?,?)",
            (order_id, user_id, name, product, rating, text),
        )
        await db.execute("UPDATE orders SET status='done' WHERE id=?", (order_id,))
        await db.commit()

async def get_reviews(limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT name, product, rating, text, created_at FROM reviews ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return await cur.fetchall()

async def avg_rating():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT AVG(rating), COUNT(*) FROM reviews")
        row = await cur.fetchone()
        return (row[0] or 0, row[1] or 0)
