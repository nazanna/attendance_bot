import sqlite3

# Создаем или открываем базу данных
conn = sqlite3.connect('current_group.db')
cursor = conn.cursor()

# Создаем таблицу, если она не существует

cursor.execute('''
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    grade INTEGER,
    group_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()