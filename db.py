import sqlite3
import threading
import os

# Thread-safe veritabanı bağlantısı için lock
db_lock = threading.Lock()

# Railway'de volume mount varsa oraya kaydet
DB_PATH = os.getenv("DB_PATH", "birthdays.db")

# Veritabanı bağlantısını oluştur
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Tablo oluştur
with db_lock:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birthdays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        chat_id INTEGER NOT NULL
    )
    """)
    conn.commit()


def execute_query(query, params=None):
    """Thread-safe sorgu çalıştırma"""
    with db_lock:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor


def fetch_all(query, params=None):
    """Thread-safe veri çekme"""
    with db_lock:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()


def fetch_one(query, params=None):
    """Thread-safe tek satır çekme"""
    with db_lock:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()