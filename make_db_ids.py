import sqlite3
from constants import workdir
# Создаем или открываем базу данных
conn = sqlite3.connect(f'{workdir}/user_ids.db')
cursor = conn.cursor()

# Создаем таблицу, если она не существует

cursor.execute('''
CREATE TABLE IF NOT EXISTS ids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    chat_id INTEGER,
    username TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()