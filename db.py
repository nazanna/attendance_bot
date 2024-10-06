import sqlite3
import aiosqlite
from functools import wraps
from constants import workdir

FILENAME = f'{workdir}/attendance.db'


def db_connection(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        conn = sqlite3.connect(FILENAME)
        cursor = conn.cursor()
        try:
            return await func(cursor, *args, **kwargs)
        finally:
            conn.commit()
            conn.close()
    return wrapper


class AttendanceDB():
    @staticmethod
    @db_connection
    async def get_student_index(cursor, chat_id: int, message_id: int):
        cursor.execute(f'''
        SELECT question_index FROM attendance WHERE user_id={chat_id} AND message_id={message_id}
        ''')
        result = cursor.fetchone()       
        if result:
            answer = result[0]
            return answer
        
    @staticmethod
    @db_connection
    async def get_student_attendance(cursor, chat_id: int, message_id: int):
        cursor.execute(f'''
        SELECT answer FROM attendance WHERE user_id={chat_id} AND message_id={message_id} ORDER BY updated_at DESC LIMIT 1
        ''')
        result = cursor.fetchone()
        if result:
            answer = result[0]
            return answer
        else:
            return -1
        
    @staticmethod
    @db_connection
    async def get_attendance_of_current_group(cursor, context, user_id):
        names = context.user_data['students_list']
        attendance = []
        for name_num in range(len(names)):
            name = names[name_num]
            cursor.execute("""
                SELECT answer
                FROM attendance 
                WHERE user_id = ? AND name = ?
                ORDER BY id DESC
                LIMIT 1
            """, (user_id, name))
            result = cursor.fetchone()
            if result:
                answer = result[0]
            attendance.append(answer)
        return names, attendance

    @staticmethod
    async def save_attendance_to_database(user_id, question_index, message_id, name, answer):
        conn = sqlite3.connect(FILENAME)
        cursor = conn.cursor()
        cursor.execute('''
                INSERT INTO attendance (user_id, question_index, message_id, name, answer) 
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, question_index, message_id, name, answer))
        conn.commit()
        conn.close()


