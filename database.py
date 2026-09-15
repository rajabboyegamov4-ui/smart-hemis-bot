import aiosqlite

DB_NAME = "hemis_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                hemis_token TEXT,
                student_id TEXT,
                full_name TEXT,
                language TEXT DEFAULT 'uz'
            )
        """)
        await db.commit()

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT hemis_token, student_id, full_name, language FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"hemis_token": row[0], "student_id": row[1], "full_name": row[2], "language": row[3]}
            return None

async def save_user(telegram_id: int, hemis_token: str, student_id: str, full_name: str, language: str = 'uz'):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, hemis_token, student_id, full_name, language)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                hemis_token=excluded.hemis_token,
                student_id=excluded.student_id,
                full_name=excluded.full_name,
                language=excluded.language
        """, (telegram_id, hemis_token, student_id, full_name, language))
        await db.commit()

async def update_language(telegram_id: int, language: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, telegram_id))
        await db.commit()
        
async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT telegram_id, hemis_token FROM users WHERE hemis_token != ''") as cursor:
            return await cursor.fetchall()
