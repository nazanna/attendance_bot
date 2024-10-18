import logging
import sqlite3
import pytz
from datetime import datetime
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters
from datetime import datetime, timedelta
from fix import fix_handler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler
from lockbox import get_lockbox_secret
from constants import token_key, started, workdir, GOOGLE_SHEET_REMINDERS_SCHEDULE_ID
import asyncio
from google_sheets_api import GoogleSheetsAPI
from helpers import parse_sheet_name
from message_handlers import Subject, choose_subject, handle_fix_buttons, choose_group, choose_grade, \
    check_attendance, update_message, complete_attendance_checking, react_to_photos
from db import AttendanceDB


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)

async def start(update: Update, context: CallbackContext):
    global started
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    context.user_data['last_message'] = update.message
    await update.message.reply_text("Здравствуйте!")
    await identify_chat(user_id, chat_id, username)
    await choose_subject(update.message)
    if update.effective_user.username in ['andr_zhi', 'nazanna25'] and not started:
        asyncio.create_task(send_notifications(context.bot))
        started = True


async def send_notifications(bot):
    sleep_duration = 5 # wakes up every X minutes and sends notifications
    schedule_data = await make_timetable()
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    next_check = now + timedelta(minutes=sleep_duration)
    next_check_time = next_check.replace(second=0, microsecond=0, minute=(next_check.minute // sleep_duration) * sleep_duration)
    await asyncio.sleep((next_check_time - now).total_seconds()) 
    print(schedule_data)
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        current_hour = now.strftime('%H')
        current_minute = now.strftime('%M')
        now_str = str(current_hour)+'.'+str(current_minute)
        if int(current_hour) % 2 == 0 and current_minute == "00":
            schedule_data = await make_timetable()
        if now_str in schedule_data:
            user_ids = schedule_data[now_str]
            for user_id in user_ids:
                await bot.send_message(chat_id=user_id, text='Сделайте фото группы и отправьте в этот чат')
                await bot.send_message(chat_id='966497557', text=f'Я отправил сообщение {user_id}')
        next_check = now + timedelta(minutes=sleep_duration)
        next_check_time = next_check.replace(second=0, microsecond=0, minute=(next_check.minute // sleep_duration) * sleep_duration)
        await asyncio.sleep((next_check_time - now).total_seconds())  # Check every 5 minutes


async def make_timetable():
    api = GoogleSheetsAPI(id = GOOGLE_SHEET_REMINDERS_SCHEDULE_ID)
    timetamble = await api.get_timetable()
    df = pd.DataFrame(timetamble, columns=['day', 'time', 'name', 'username'])
    day_of_week = datetime.now(pytz.timezone('Europe/Moscow')).weekday()
    days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    today = days[day_of_week]
    today_timetable = df[df['day']==today]
    map_timetable_today = {}
    for _, row in today_timetable.iterrows():
        if row['username']:
            username = str(row['username'])[1:]
            conn = sqlite3.connect(f'{workdir}/user_ids.db')
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
                answer = result[0]

                if row['time'] not in map_timetable_today:
                    map_timetable_today[row['time']]=[answer]
                else:
                    map_timetable_today[row['time']].append(answer)
    return map_timetable_today


async def identify_chat(user_id, chat_id, username):
    conn = sqlite3.connect(f'{workdir}/user_ids.db')
    cursor = conn.cursor()
    cursor.execute('''
            INSERT INTO ids (user_id, chat_id, username) 
            VALUES (?, ?, ?)
            ''', (user_id, chat_id, username)) 
    conn.commit()
    conn.close()



async def get_current_list_of_students(context):
    api = GoogleSheetsAPI()
    return await api.get_list_of_students(await parse_sheet_name(context))



async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    if query.data.__contains__("attendance"):
        await handle_fix_buttons(update, context)
    else:
        data = query.data.split("_")
        response_type = data[1]
        response = int(data[2])

        match response_type:
            case 'subject':
                context.user_data['subject'] = response
                match Subject(response):
                    case Subject.PROF_SEMINAR:
                        await choose_grade(query.message, user_id, context)
                    case Subject.OLIMP_PRACTICE:
                        await choose_grade(query.message, user_id, context)
                    case Subject.BASE_PRACTICE:
                        await choose_group(query.message, user_id, context)
                    case Subject.MECHANICS:
                        context.user_data['question_index'] = 0
                        context.user_data['students_list'] = await get_current_list_of_students(context)
                        await check_attendance(query.message, user_id, context)
                    case Subject.IPHO_PREP:
                        context.user_data['question_index'] = 0
                        context.user_data['students_list'] = await get_current_list_of_students(context)
                        await check_attendance(query.message, user_id, context)
            case 'grade':
                grade = response
                context.user_data['grade'] = grade
                if grade == 11 and Subject(context.user_data['subject']) == Subject.PROF_SEMINAR:
                    context.user_data['question_index'] = 0
                    context.user_data['group'] = 1
                    await check_attendance(query.message, user_id, context)
                else:
                    await choose_group(query.message, user_id, context)

            case 'group':
                group = response
                context.user_data['group'] = group
                context.user_data['question_index'] = 0
                context.user_data['students_list'] = await get_current_list_of_students(context)
                await check_attendance(query.message, user_id, context)
            
            case _:
                question_index = int(response_type)
                await update_message(user_id, query.message.message_id, question_index, int(response), context)
                await AttendanceDB.save_attendance_to_database(user_id, question_index, query.message.message_id, context.user_data['students_list'][question_index], int(response))
                if question_index == context.user_data['question_index']:
                    context.user_data['question_index'] += 1
                    if context.user_data['question_index'] < len(context.user_data['students_list']):
                        await check_attendance(query.message, user_id, context)
                    else:                 
                        await complete_attendance_checking(query.message, context)
            

def main():
    token = get_lockbox_secret(token_key)
    app = ApplicationBuilder().token(token).build()
    print("Bot successfully started!")
    app.add_handler(CommandHandler('start', start))
    app.add_handler(fix_handler)
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, react_to_photos))
    app.run_polling()
    app.idle()

if __name__ == '__main__':
    main()