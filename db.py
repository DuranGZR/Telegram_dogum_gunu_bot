import sqlite3

conn = sqlite3.connect("birthdays.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    chat_id INTEGER NOT NULL
)
""")

conn.commit()