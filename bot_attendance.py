import logging
import sqlite3
from datetime import datetime
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
import asyncio
import threading
import schedule
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import gspread
from google.oauth2.service_account import Credentials
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
# from lockbox import get_lockbox_secret
# from questions import QUESTIONS, IMAGES, number_of_questions_in_first_poll
# from constants import users_db_name, responses_db_name, token_key

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)
token = '7907658286:AAFRA1vGrsFyaHlUGOuZUeE2LKUQDPZPyEM'
file_name = 'списки.xlsx'

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    context.user_data['last_message'] = update.message
    await update.message.reply_text("Добрый день!")
    await identify_chat(user_id, chat_id, username)
    await choose_subject(update.message)

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
            questions_1 = ['Выберите класс']
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
    sheet_name = make_sheet_name(context)
    df = pd.read_excel(file_name, sheet_name=sheet_name)
    surnames = df['Фамилия'].tolist()
    names = df['Имя'].tolist()
    questions = [surnames[i]+' '+names[i] for i in range(len(surnames))]
    return questions

async def check_attendance(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    question_index = context.user_data['question_index']
    questions = make_list_kids(context)
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
    df = pd.read_excel(file_name, sheet_name=sheet_name)
    df[current_date_str] = 0
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    names = make_list_kids(context)
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
        df.at[name_num, current_date_str] = answer
    with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
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
            await check_attendance(query.message, user_id, context)
        
        case _:
            await save_attendance(user_id, username, int(question), make_list_kids(context)[int(question)], int(response))
            context.user_data['question_index'] += 1
            if context.user_data['question_index']<len(make_list_kids(context)):
                await check_attendance(query.message, user_id, context)
            else: 
                await query.message.reply_text("Ура! Вы отметили посещаемость!")
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
    # token = get_lockbox_secret(token_key)
    app = ApplicationBuilder().token(token).build()
    print("Bot successfully started!")
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
    thread = threading.Thread(target=schedule_messages)
    thread.start()

    app.idle()

if __name__ == '__main__':
    main()