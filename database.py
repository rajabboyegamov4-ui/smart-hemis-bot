import sqlite3

def init_db():
    """Baza va jadvalni yaratish (birinchi marta ishga tushganda)"""
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            hemis_login TEXT,
            hemis_password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_user(telegram_id, login, password):
    """Talabani bazaga qo'shish yoki yangilash"""
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute('''
        REPLACE INTO users (telegram_id, hemis_login, hemis_password)
        VALUES (?, ?, ?)
    ''', (telegram_id, login, password))
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
