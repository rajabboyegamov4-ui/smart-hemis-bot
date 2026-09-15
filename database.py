import aiosqlite

DB_NAME = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                hemis_token TEXT,
                student_id TEXT,
                full_name TEXT
            )
        """)
        await db.commit()

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchone()

async def save_user(telegram_id: int, hemis_token: str, student_id: str, full_name: str = ""):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, hemis_token, student_id, full_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                hemis_token = excluded.hemis_token,
                student_id = excluded.student_id,
                full_name = excluded.full_name
        """, (telegram_id, hemis_token, student_id, full_name))
        await db.commit()