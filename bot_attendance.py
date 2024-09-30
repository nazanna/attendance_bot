import logging
import sqlite3
import pytz
from datetime import datetime
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
from datetime import datetime, timedelta
from fix import fix_handler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
from lockbox import get_lockbox_secret
# from questions import QUESTIONS, IMAGES, number_of_questions_in_first_poll
from constants import token_key, started, workdir
import asyncio
from google_sheets_api import GoogleSheetsAPI
from helpers import parse_sheet_name
from fix import fix
from helpers import save_attendance

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)

async def start(update: Update, context: CallbackContext):
    global started
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    context.user_data['last_message'] = update.message
    await update.message.reply_text("Добрый день!")
    await identify_chat(user_id, chat_id, username)
    await choose_subject(update.message)
    if update.effective_user.username in ['andr_zhi', 'nazanna25'] and not started:
        asyncio.create_task(send_reminders(context.bot))
        started = True


async def send_reminders(bot):
    round_up = 5
    schedule_data = await make_timetable()
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    next_check = now + timedelta(minutes=round_up)
    next_check_time = next_check.replace(second=0, microsecond=0, minute=(next_check.minute // round_up) * round_up)
    await asyncio.sleep((next_check_time - now).total_seconds()) 
    print(schedule_data)
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        current_hour = now.strftime('%H')  # Часы
        current_minute = now.strftime('%M') 
        now_str = str(current_hour)+'.'+str(current_minute)
        if int(current_hour) % 2 == 0 and current_minute == "00":
            schedule_data = await make_timetable()
        if now_str in schedule_data:
            user_ids = schedule_data[now_str]
            for user_id in user_ids:
                await bot.send_message(chat_id=user_id, text='Отметьте посещаемость на занятии! Для этого нужно нажать /start')
                await bot.send_message(chat_id='966497557', text=f'Я отправил сообщение {user_id}')
        next_check = now + timedelta(minutes=round_up)
        next_check_time = next_check.replace(second=0, microsecond=0, minute=(next_check.minute // round_up) * round_up)
        await asyncio.sleep((next_check_time - now).total_seconds())  # Check every 5 minutes


async def make_timetable():
    api = GoogleSheetsAPI(id = '1-y3cE_AIhA8VuRkax-E9-4mSWo4UpnPyxWeFvERHLM4')
    timetamble = await api.get_timetable()
    df = pd.DataFrame(timetamble, columns=['day', 'time', 'name', 'username'])
    day_of_week = datetime.now(pytz.timezone('Europe/Moscow')).weekday()
    days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    today = days[day_of_week]
    today_timetable = df[df['day']==today]
    map_timetable_today = {}
    for index, row in today_timetable.iterrows():
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
                match context.user_data['grade']:
                    case 7:
                        name1 = 'Безбородов '
                        name2 = 'Черникова '
                    case 8:
                        name1 = 'Вахитов '
                        name2 = 'Степушин/Черников ' 
                    case 9:
                        name1 = 'Бердникова/Тясин '
                        name2 = 'Степушин/Черников '
                    case 10:
                        name1 = 'Бердникова/Гук '
                        name2 = 'Пивоварчик '
                keyboard = [
                    [InlineKeyboardButton(name1, callback_data=f"response_group_1")],
                    [InlineKeyboardButton(name2, callback_data=f"response_group_2")],
                ]
            if context.user_data['subject'] == 2:
                 keyboard = [
                    [InlineKeyboardButton("7", callback_data=f"response_group_7"),
                    InlineKeyboardButton("8-9", callback_data=f"response_group_89")],
                ]
            if context.user_data['subject'] == 3:
                match context.user_data['grade']:
                    case 7:
                        keyboard = [
                        [InlineKeyboardButton("Среда, Кригер", callback_data=f"response_group_1")],
                        [InlineKeyboardButton("Суббота, Киселевская", callback_data=f"response_group_2")],
                        [InlineKeyboardButton("Суббота, Степанов", callback_data=f"response_group_3")]
                    ]
                    case 8:
                        keyboard = [
                        [InlineKeyboardButton("Понедельник, Кригер", callback_data=f"response_group_1")],
                        [InlineKeyboardButton("Понедельник, Шадрин", callback_data=f"response_group_3")],
                        [InlineKeyboardButton("Четверг, Киселевская", callback_data=f"response_group_2")]
                    ]
                    case 9:
                        keyboard = [
                        [InlineKeyboardButton("Вторник, Назарчук", callback_data=f"response_group_4")],
                        [InlineKeyboardButton("Среда, Киселевский", callback_data=f"response_group_3")],
                        [InlineKeyboardButton("Среда, Тихонов", callback_data=f"response_group_1")],
                        [InlineKeyboardButton("Четверг, Тихонов", callback_data=f"response_group_2")]
                        
                    ]
                    case 10:
                        keyboard = [
                        [InlineKeyboardButton("Пятница, Киселевский", callback_data=f"response_group_1")],
                        [InlineKeyboardButton("Суббота, Киселевский", callback_data=f"response_group_2")],
                        [InlineKeyboardButton("Суббота, Тихонов", callback_data=f"response_group_3")],
                    ]    
                    case 11:
                        keyboard = [
                        [InlineKeyboardButton("Вторник, Тихонов", callback_data=f"response_group_1")],
                        [InlineKeyboardButton("Вторник, Еськин", callback_data=f"response_group_3")],
                        [InlineKeyboardButton("Пятница, Тихонов", callback_data=f"response_group_2")]
                    ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text('Выберите группу', reply_markup=reply_markup)


async def make_list_kids(context):
    api = GoogleSheetsAPI()
    return await api.get_list_of_students(await parse_sheet_name(context))


async def check_attendance(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    question_index = context.user_data['question_index']
    questions = context.user_data['list']
    keyboard = [
                [InlineKeyboardButton("Присутствует", callback_data=f"response_{question_index}_1"),
                InlineKeyboardButton("Отсутствует", callback_data=f"response_{question_index}_0")],
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(questions[question_index], reply_markup=reply_markup)


async def suggest_fixes(attendance_list, message, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
                [InlineKeyboardButton("Все верно", callback_data=f"confirm_attendance_save"),
                InlineKeyboardButton("Исправить", callback_data=f"fix_attendance")],
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    answer = """Вот получившийся список посещаемости. Проверьте его, пожалуйста, и нажмите соответствующую кнопку в конце сообщения.\n"""
    for att in attendance_list:
        answer += att + '\n'
    await message.reply_text(answer, reply_markup=reply_markup)


async def get_attendance_of_current_group(context, user_id):
    conn = sqlite3.connect(f'{workdir}/attendance.db')
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
    conn.close()
    return names, att


async def save_attendance_to_google_sheets(context, user_id):
    _, attendance = await get_attendance_of_current_group(context, user_id)
    sheet_name = await parse_sheet_name(context)
    api = GoogleSheetsAPI()
    await api.insert_attendance(sheet_name, attendance)

async def update_attendance_to_google_sheets(context, user_id):
    _, attendance = await get_attendance_of_current_group(context, user_id)
    sheet_name = await parse_sheet_name(context)
    api = GoogleSheetsAPI()
    await api.update_last_attendance(sheet_name, attendance)


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    if query.data == "confirm_attendance_save":
        await save_attendance_to_google_sheets(context, user_id)
        await query.message.reply_text("Спасибо, что отметили посещаемость! Этот котик очень этому рад!")
        with open(f"{workdir}/final.jpg", "rb") as image:
            await query.message.reply_photo(photo=image)

    elif query.data == "confirm_attendance_update":
        await save_attendance_to_google_sheets(context, user_id)
        await query.message.reply_text("Спасибо, что отметили посещаемость! Этот котик очень этому рад!")
        with open(f"{workdir}/final.jpg", "rb") as image:
            await query.message.reply_photo(photo=image)

    
    elif query.data == "fix_attendance":
        await query.message.reply_text("Нажмите на команду /fix, чтобы исправить посещаемость.")

    else:
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
                        context.user_data['list'] = await make_list_kids(context)
                        await check_attendance(query.message, user_id, context)
                    case 5:
                        context.user_data['question_index'] = 0
                        context.user_data['list'] = await make_list_kids(context)
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
                context.user_data['list'] = await make_list_kids(context)
                await check_attendance(query.message, user_id, context)
            
            case _:
                await save_attendance(user_id, int(question), context.user_data['list'][int(question)], int(response))
                context.user_data['question_index'] += 1
                if context.user_data['question_index'] < len(context.user_data['list']):
                    await check_attendance(query.message, user_id, context)
                else:                 
                    names, attendance = await get_attendance_of_current_group(context, user_id)
                    attendance_list = [f'{name} {"Да" if a == 1 else "Нет"}' for name, a in zip(names, attendance)]
                    await suggest_fixes(attendance_list, query.message, context)
            

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