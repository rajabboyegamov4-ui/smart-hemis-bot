import sqlite3

def init_db():
    """Baza va jadvalni yaratish (til ustuni bilan)"""
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            hemis_login TEXT,
            hemis_password TEXT,
            language TEXT DEFAULT 'uz'
        )
    ''')
    conn.commit()
    conn.close()

def save_user(telegram_id, login, password):
    """Talabani bazaga qo'shish yoki yangilash (oldingi tilini saqlagan holda)"""
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    
    # Agar foydalanuvchi oldindan bo'lsa, uning tanlagan tilini saqlab qolamiz
    cursor.execute("SELECT language FROM users WHERE telegram_id = ?", (telegram_id,))
    res = cursor.fetchone()
    lang = res[0] if res else 'uz'

    cursor.execute('''
        REPLACE INTO users (telegram_id, hemis_login, hemis_password, language)
        VALUES (?, ?, ?, ?)
    ''', (telegram_id, login, password, lang))
    conn.commit()
    conn.close()

def get_user(telegram_id):
    """Talabaning login va parolini bazadan olish"""
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT hemis_login, hemis_password FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_language(telegram_id, lang):
    """Foydalanuvchining tanlagan tilini bazada yangilash"""
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (lang, telegram_id))
    conn.commit()
    conn.close()

def get_user_language(telegram_id):
    """Foydalanuvchining joriy tilini olish (agar topilmasa 'uz' qaytaradi)"""
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE telegram_id = ?", (telegram_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 'uz'
