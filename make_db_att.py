import sqlite3
from constants import workdir
# Создаем или открываем базу данных
conn = sqlite3.connect(f'{workdir}/attendance.db')
cursor = conn.cursor()

# Создаем таблицу, если она не существует

cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    question_index INTEGER,
    name TEXT,
    answer INTEGER,  
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()