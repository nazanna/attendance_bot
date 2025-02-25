from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from telegram.ext import ContextTypes
from datetime import datetime
from constants import GOOGLE_SHEET_REMINDERS_SCHEDULE_ID, users_db_name
from google_sheets_api import GoogleSheetsAPI
from pytz import timezone

REMINDER_MESSAGE = "Пожалуйста, заполните посещаемость (для этого надо нажать /start)"

async def callback_message(context: ContextTypes.DEFAULT_TYPE):
    global REMINDER_MESSAGE
    await context.bot.send_message(chat_id=context.job.data['chat_id'], text=REMINDER_MESSAGE)

def schedule_notifications(app):
    api = GoogleSheetsAPI(id = GOOGLE_SHEET_REMINDERS_SCHEDULE_ID)
    raw_timetamble = api.get_timetable()
    timetable = pd.DataFrame(raw_timetamble, columns=['day', 'name', 'time', 'username'])
    for _, row in timetable.iterrows():
        current_day = row['day'].split('.')
        current_time = row['time'].split(':')
        if not row['username']:
            continue
        username = row['username'][1:]
        conn = sqlite3.connect(users_db_name)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT chat_id
        FROM ids 
        WHERE username = ?
        ORDER BY updated_at DESC
        LIMIT 1
    """, [username])
        result = cursor.fetchone()
        if result:
            chat_id = result[0]

            when_to_send = datetime(day=int(current_day[0]), month=int(current_day[1]), year=int(current_day[2]), hour=int(current_time[0]), minute=int(current_time[1]), tzinfo=timezone('Europe/Moscow'))
            delta=when_to_send-datetime.now(tz=timezone('Europe/Moscow'))-timedelta(minutes=30)
            if delta.total_seconds() > 0:
                app.job_queue.run_once(callback_message, when=delta, data = {'chat_id': chat_id})
                print(row['username'], " scheduled! ", when_to_send, "Will be sent in", delta.seconds)
