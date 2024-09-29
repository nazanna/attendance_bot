import logging
import sqlite3
import pytz
from datetime import datetime
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
import threading
import locale
from datetime import datetime, timedelta
from fix import fix_handler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from google.oauth2.service_account import Credentials
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
from lockbox import get_lockbox_secret
# from questions import QUESTIONS, IMAGES, number_of_questions_in_first_poll
from constants import token_key
import asyncio
from google_sheets_api import GoogleSheetsAPI


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)
token = 'attendance-bot-test-token'
file_name = 'списки.xlsx'

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    context.user_data['last_message'] = update.message
    await update.message.reply_text("Добрый день!")
    await identify_chat(user_id, chat_id, username)
    await choose_subject(update.message)
    asyncio.create_task(send_reminders(context))

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    schedule_data = make_timetable()
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    next_check = now + timedelta(minutes=5)
    next_check_time = next_check.replace(second=0, microsecond=0, minute=(next_check.minute // 5) * 5)
    await asyncio.sleep((next_check_time - now).total_seconds()) 

    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        current_hour = now.strftime('%H')  # Часы
        current_minute = now.strftime('%M') 
        now = str(current_hour)+':'+str(current_minute)
        if now in schedule_data:
            usernames = schedule_data[now]
            for username in usernames:
                await context.bot.send_message(chat_id=username, text='Отметьте посещаемость на занятии! Для этого нужно нажать /start')
        next_check = now + timedelta(minutes=5)
        next_check_time = next_check.replace(second=0, microsecond=0, minute=(next_check.minute // 5) * 5)
        await asyncio.sleep((next_check_time - now).total_seconds())  # Check every 5 minutes


def make_timetable():
    api = GoogleSheetsAPI(id = '1-y3cE_AIhA8VuRkax-E9-4mSWo4UpnPyxWeFvERHLM4')
    timetamble = api.get_timetable()
    df = pd.DataFrame(timetamble, columns=['day', 'time', 'name', 'username'])
    today = datetime.today()
    day_of_week = today.weekday()
    days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    # today = days[day_of_week]
    today = 'вт'
    today_timetable = df[df['day']==today]
    map_timetable_today = {}
    for index, row in today_timetable.iterrows():
        if row['username']:
            username = str(row['username'])[1:]
            conn = sqlite3.connect('user_ids.db')
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
    # print("Сегодня:", days[day_of_week])
    # print(df)

async def identify_chat(user_id, chat_id, username):
    conn = sqlite3.connect('user_ids.db')
    cursor = conn.cursor()
    cursor.execute('''
            INSERT INTO ids (user_id, chat_id, username) 
            VALUES (?, ?, ?)
            ''', (user_id, chat_id, username)) 
    print('here')
    conn.commit()
    conn.close()
async def choose_subject(message):
    keyboard = [
                [InlineKeyboardButton("Профильный семинар", callback_data=f"response_subject_1")],
                [InlineKeyboardButton("Базовый прак", callback_data=f"response_subject_2")],
                [InlineKeyboardButton("Олимпиадный прак", callback_data=f"response_subject_3")],
                [InlineKeyboardButton("Механика", callback_data=f"response_subject_4")],
                [InlineKeyboardButton("Преподготовка к IPhO", callback_data=f"response_subject_5")],
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text('Выберите вид занятия', reply_markup=reply_markup)

async def choose_grade(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
            keyboard = [
                [InlineKeyboardButton("7", callback_data=f"response_grade_7"),
                InlineKeyboardButton("8", callback_data=f"response_grade_8"),
                InlineKeyboardButton("9", callback_data=f"response_grade_9"),
                InlineKeyboardButton("10", callback_data=f"response_grade_10"),
                InlineKeyboardButton("11", callback_data=f"response_grade_11")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text('Выберите класс', reply_markup=reply_markup)


async def choose_group(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
            if context.user_data['subject'] == 1:
                keyboard = [
                    [InlineKeyboardButton("1", callback_data=f"response_group_1"),
                    InlineKeyboardButton("2", callback_data=f"response_group_2")],
                ]
            if context.user_data['subject'] == 2:
                 keyboard = [
                    [InlineKeyboardButton("7", callback_data=f"response_group_7"),
                    InlineKeyboardButton("8-9", callback_data=f"response_group_89")],
                ]
            if context.user_data['subject'] == 3:
                if context.user_data['grade'] == 9:
                    keyboard = [
                        [InlineKeyboardButton("1", callback_data=f"response_group_1"),
                        InlineKeyboardButton("2", callback_data=f"response_group_2"),
                        InlineKeyboardButton("3", callback_data=f"response_group_3"),
                        InlineKeyboardButton("4", callback_data=f"response_group_4")],
                    ]
                else:
                  keyboard = [
                        [InlineKeyboardButton("1", callback_data=f"response_group_1"),
                        InlineKeyboardButton("2", callback_data=f"response_group_2"),
                        InlineKeyboardButton("3", callback_data=f"response_group_3")],
                    ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text('Выберите группу', reply_markup=reply_markup)

def make_sheet_name(context):
    subject = context.user_data['subject']
    match subject:
        case 1:
            grade = context.user_data['grade']
            group = context.user_data['group']
            sheet_name = str(grade)+'_'+str(group)
        case 2:
            group = context.user_data['group']
            if group == 7:
                sheet_name='7_баз_прак'
            else:
                sheet_name = '8_9_баз_прак'
        case 3:
            grade = context.user_data['grade']
            group = context.user_data['group']
            sheet_name = str(grade)+'_ол_прак_'+str(group)
        case 4:
            sheet_name = 'Механика'
        case 5:
            sheet_name = 'Преподготовка к IPhO'
    return sheet_name

def make_list_kids(context):
    api = GoogleSheetsAPI()
    return api.get_list_of_students(make_sheet_name(context))

async def check_attendance(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    question_index = context.user_data['question_index']
    questions = context.user_data['list']
    keyboard = [
                [InlineKeyboardButton("Присутствует", callback_data=f"response_{question_index}_1"),
                InlineKeyboardButton("Отсутствует", callback_data=f"response_{question_index}_0")],
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(questions[question_index], reply_markup=reply_markup)




async def save_attendance(user_id, username, question_index, name, answer):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('''
            INSERT INTO attendance (user_id, username, question_index, name, answer) 
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, question_index, name, answer))
    conn.commit()
    conn.close()


def make_norm_data(context, user_id):
    sheet_name = make_sheet_name(context)
    current_date_str = datetime.now().strftime("%d %m")
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    names = context.user_data['list']
    att = []
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
        att.append(answer)
    api = GoogleSheetsAPI()
    api.insert_attendance(sheet_name, att)
    conn.close()
    print(current_date_str)


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    username = update.effective_user.username
    await query.answer()

    data = query.data.split("_")
    question = (data[1])
    response = int(data[2])

    match question:
        case 'subject':
            context.user_data['subject'] = response
            match response:
                case 1:
                    await choose_grade(query.message, user_id, context)
                case 3:
                    await choose_grade(query.message, user_id, context)
                case 2:
                    await choose_group(query.message, user_id, context)
                case 4:
                    context.user_data['question_index'] = 0
                    await check_attendance(query.message, user_id, context)
                case 5:
                    context.user_data['question_index'] = 0
                    await check_attendance(query.message, user_id, context)

        case 'grade':
            context.user_data['grade'] = response
            if response == 11 and context.user_data['subject']==1:
                context.user_data['question_index'] = 0
                context.user_data['group'] = 1
                await check_attendance(query.message, user_id, context)
            else:
                await choose_group(query.message, user_id, context)

        case 'group':
            context.user_data['group'] = response
            context.user_data['question_index'] = 0
            context.user_data['list'] = make_list_kids(context)
            await check_attendance(query.message, user_id, context)
        
        case _:
            await save_attendance(user_id, username, int(question), context.user_data['list'][int(question)], int(response))
            context.user_data['question_index'] += 1
            if context.user_data['question_index']<len(context.user_data['list']):
                await check_attendance(query.message, user_id, context)
            else: 
                await query.message.reply_text("Спасибо, что отметили посещаемость! Этот котик очень этому рад!")
                with open("final.jpg", "rb") as image:
                    await query.message.reply_photo(photo=image)
                make_norm_data(context, user_id)
        

# def send_message(context: CallbackContext):
#     chat_id = ''
#     last_message = context.user_data.get('last_message')
#     if chat_id is not None:
#         last_message.reply_text("Запланированное сообщение!")

# def schedule_messages():
#     # Пример: отправка сообщений по дням недели
#     schedule.every().monday.at("09:00").do(send_message, "Сообщение на понедельник!")
#     schedule.every().tuesday.at("09:00").do(send_message, "Сообщение на вторник!")
#     schedule.every().wednesday.at("09:00").do(send_message, "Сообщение на среду!")
#     schedule.every().thursday.at("09:00").do(send_message, "Сообщение на четверг!")
#     schedule.every().friday.at("09:00").do(send_message, "Сообщение на пятницу!")

#     while True:
#         schedule.run_pending()
#         time.sleep(1)




def main():
    token = get_lockbox_secret(token_key)
    app = ApplicationBuilder().token(token).build()
    print("Bot successfully started!")
    app.add_handler(CommandHandler('start', start))
    app.add_handler(fix_handler)
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

    app.idle()

if __name__ == '__main__':
    main()