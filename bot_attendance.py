import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
from fix import fix_handler
from telegram import Update
from lockbox import get_lockbox_secret
from constants import token_key, started, workdir
from google_sheets_api import GoogleSheetsAPI
from helpers import parse_sheet_name
from message_handlers import Subject, handle_fix_buttons, choose_group, choose_grade, \
    check_attendance, update_message, complete_attendance_checking, react_to_photos
from db import AttendanceDB
from notifications import schedule_notifications

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
    await choose_grade(update.message, user_id, context)

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

async def schedule(update: Update, context: CallbackContext):
    if update.effective_user.username not in ['andr_zhi','nazanna25']:
        return
    await context.bot.send_message(text="Началось обновление уведомлений, подождите немного", chat_id= update.effective_user.id)

    for job in context.job_queue.jobs():
        job.schedule_removal()
    schedule_notifications(context)
    await context.bot.send_message(text="Уведомления успешно обновлены!", chat_id= update.effective_user.id)

def main():
    token = get_lockbox_secret(token_key)
    app = ApplicationBuilder().token(token).build()
    schedule_notifications(app)
    print("Bot successfully started!")
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('schedule', schedule))
    app.add_handler(fix_handler)
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, react_to_photos))
    app.run_polling()
    app.idle()

if __name__ == '__main__':
    main()