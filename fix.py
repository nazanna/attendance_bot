import re
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from google_sheets_api import GoogleSheetsAPI
from helpers import parse_sheet_name
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from db import AttendanceDB

WAITING_FOR_MESSAGE = 0

EXPECTED_FORMAT = r'^([а-яА-ЯёЁ]+)\s+([а-яА-ЯёЁ]+)\s+(Да|Нет)$'


async def fix(update: Update, context: CallbackContext) -> int:
    """Start the fix command and ask for the user's message."""
    keyboard = [
                [InlineKeyboardButton("Все верно", callback_data=f"confirm_attendance_update")
                ],
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    answer = '''Исправьте посещаемость, нажав на кнопку возле ученика. После этого подтвердите исправление кнопкой снизу'''
    await update.message.reply_text(answer, reply_markup=reply_markup)



async def index_of_student_in_group(group, first_name, last_name) -> int:
    fullname = f'{last_name} {first_name}'
    api = GoogleSheetsAPI()
    students = await api.get_list_of_students(group)
    try:
        return students.index(fullname)
    except ValueError:
        return -1
        

async def check_message(update: Update, context: CallbackContext) -> int:
    """Check the user's message and respond accordingly."""
    user_message = update.message.text
    match = re.search(EXPECTED_FORMAT, user_message)

    if match:
        last_name = match.group(1)
        first_name = match.group(2)
        group = await parse_sheet_name(context)
        new_value = match.group(3) 
        index_of_student = await index_of_student_in_group(group, first_name, last_name)
        if index_of_student == -1:
            await update.message.reply_text("Такого ученика не существует, пожалуйста, проверьте правильность написания")
        else:
            await AttendanceDB.save_attendance_to_database(update.effective_user.id, index_of_student, update.message.message_id, f'{last_name} {first_name}', 1 if new_value=="Да" else 0)
            keyboard = [
                [InlineKeyboardButton("Хватит", callback_data=f"confirm_attendance_update"),
                InlineKeyboardButton("Исправить еще", callback_data=f"fix_attendance")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text("Исправлено!", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Пожалуйста, повторите отправку сообщения в правильном формате.")

    # End the conversation after processing the message
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the conversation."""
    await update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

fix_handler = ConversationHandler(
    entry_points=[CommandHandler("fix", fix)],
    states={
        WAITING_FOR_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_message)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)
