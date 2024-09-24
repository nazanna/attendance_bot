import logging
import sqlite3
from datetime import datetime
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    username = update.effective_user.username
    await update.message.reply_text("Привет! Сейчас начнется большой опрос. Пожалуйста, отвечайте честно и думайте перед выбором! Введите /poll_1_part, чтобы начать.")
    await choose_grade(update.message, user_id, context)

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
            keyboard = [
                [InlineKeyboardButton("1", callback_data=f"response_group_1"),
                InlineKeyboardButton("2", callback_data=f"response_group_2"),
                InlineKeyboardButton("3", callback_data=f"response_group_3")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text('Выберите группу', reply_markup=reply_markup)

def identify_group(user_id):
    connection = sqlite3.connect('current_group.db')
    cursor = connection.cursor()
    cursor.execute("""
    SELECT group_id 
    FROM groups 
    WHERE user_id = ? 
    ORDER BY id DESC
    LIMIT 1
""", (user_id,))
    result = cursor.fetchone()
    if result:
        group_id = result[0]
    cursor.execute("""
    SELECT grade
    FROM groups 
    WHERE user_id = ? 
    ORDER BY id DESC
    LIMIT 1
""", (user_id,))
    result = cursor.fetchone()
    if result:
        grade = result[0]
    return grade, group_id


def make_list_kids(user_id: int):
    sheet_name = str(identify_group(user_id)[0])+'_'+str(identify_group(user_id)[1])
    df = pd.read_excel(file_name, sheet_name=sheet_name)
    surnames = df['Фамилия'].tolist()
    names = df['Имя'].tolist()
    questions = [surnames[i]+' '+names[i] for i in range(len(surnames))]
    return questions

async def check_attendance(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    question_index = context.user_data['question_index']
    questions = make_list_kids(user_id)
    keyboard = [
                [InlineKeyboardButton("Присутствует", callback_data=f"response_{question_index}_1"),
                InlineKeyboardButton("Отсутствует", callback_data=f"response_{question_index}_0")],
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(questions[question_index], reply_markup=reply_markup)

async def save_group(user_id: int, username: str, grade: int, group: int):
    conn = sqlite3.connect('current_group.db')
    cursor = conn.cursor()
    if group == -1:
        cursor.execute('''
            INSERT INTO groups (user_id, username, grade, group_id) 
            VALUES (?, ?, ?, ?)
            ''', (user_id, username, grade, group)) # TODO: check
    else:
        cursor.execute("""
    UPDATE groups 
    SET group_id = ? 
    WHERE rowid = (
        SELECT rowid 
        FROM groups 
        WHERE user_id = ? 
        ORDER BY id DESC
        LIMIT 1
    )
""", (group, user_id))
    conn.commit()
    conn.close()

async def save_attendance(user_id, username, question_index, name, answer):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('''
            INSERT INTO attendance (user_id, username, question_index, name, answer) 
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, question_index, name, answer))
    conn.commit()
    conn.close()

def make_norm_data(user_id):
    sheet_name = str(identify_group(user_id)[0])+'_'+str(identify_group(user_id)[1])
    current_date_str = datetime.now().strftime("%d %m")
    df = pd.read_excel(file_name, sheet_name=sheet_name)
    df[current_date_str] = 0
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    names = make_list_kids(user_id)
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
    df.to_excel(file_name, sheet_name=sheet_name, index=False)
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
        case 'grade':
            await save_group(user_id, username, response, -1)
            await choose_group(query.message, user_id, context)

        case 'group':
            await save_group(user_id, username, -1, response)
            context.user_data['question_index'] = 0
            await check_attendance(query.message, user_id, context)
        
        case _:
            await save_attendance(user_id, username, int(question), make_list_kids(user_id)[int(question)], int(response))
            context.user_data['question_index'] += 1
            if context.user_data['question_index']<len(make_list_kids(user_id)):
                await check_attendance(query.message, user_id, context)
            else: 
                await query.message.reply_text("Ура! Вы отметили посещаемость!")
                make_norm_data(user_id)
        

def main():
    # token = get_lockbox_secret(token_key)
    app = ApplicationBuilder().token(token).build()
    print("Bot successfully started!")
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
    app.idle()

if __name__ == '__main__':
    main()