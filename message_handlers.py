from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from enum import Enum
from google_sheets_api import GoogleSheetsAPI
from google_drive_api import GoogleDriveAPI
from helpers import parse_sheet_name
from constants import workdir
from db import AttendanceDB


class Subject(Enum):
    PROF_SEMINAR=1
    BASE_PRACTICE=2
    OLIMP_PRACTICE=3
    MECHANICS=4
    IPHO_PREP=5


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
    subject = Subject(context.user_data['subject'])
    if subject == Subject.PROF_SEMINAR:
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
    if subject == Subject.BASE_PRACTICE:
            keyboard = [
            [InlineKeyboardButton("7", callback_data=f"response_group_7"),
            InlineKeyboardButton("8-9", callback_data=f"response_group_89")],
        ]
    if subject == Subject.OLIMP_PRACTICE:
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




async def check_attendance(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    question_index = context.user_data['question_index']
    questions = context.user_data['students_list']
    keyboard = [
                [InlineKeyboardButton("Присутствует", callback_data=f"response_{question_index}_1"),
                InlineKeyboardButton("Отсутствует", callback_data=f"response_{question_index}_0")],
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(questions[question_index], reply_markup=reply_markup)


async def complete_attendance_checking(message, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
                [InlineKeyboardButton("Все верно", callback_data=f"confirm_attendance_save")
                ],
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    answer = """Вы отметили посещаемость! Пожалуйста, проверьте, что все верно, исправьте при необходимости \
и затем нажмите кнопку под этим сообщением. Если потом будет нужно что-то исправить, просто нажмите /fix."""
    await message.reply_text(answer, reply_markup=reply_markup)


async def save_attendance_to_google_sheets(context, user_id):
    _, attendance = await AttendanceDB.get_attendance_of_current_group(context, user_id)
    sheet_name = await parse_sheet_name(context)
    api = GoogleSheetsAPI()
    await api.insert_attendance(sheet_name, attendance)


async def update_attendance_in_google_sheets(context, user_id):
    _, attendance = await AttendanceDB.get_attendance_of_current_group(context, user_id)
    sheet_name = await parse_sheet_name(context)
    api = GoogleSheetsAPI()
    await api.update_last_attendance(sheet_name, attendance)


async def handle_fix_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    if query.data == "confirm_attendance_save":
        await query.message.reply_text("Спасибо, что отметили посещаемость! Этот котик очень этому рад!")
        with open(f"{workdir}/final.jpg", "rb") as image:
            await query.message.reply_photo(photo=image)
        await save_attendance_to_google_sheets(context, user_id)

    elif query.data == "confirm_attendance_update":
        await query.message.reply_text("Спасибо! Если надо исправить что-то еще, просто нажмите /fix.")
        await update_attendance_in_google_sheets(context, user_id)

    
    elif query.data == "fix_attendance":
        await query.message.reply_text("Нажмите на команду /fix, чтобы исправить посещаемость.")



async def update_message(chat_id, message_id, student_index, response, context: CallbackContext):
    previous_attendance = await AttendanceDB.get_student_attendance(chat_id, message_id)
    if previous_attendance == response:
        return
    attendance_symbol = "✅" if response == 1 else "❌"
    new_text = f"{attendance_symbol} {context.user_data['students_list'][student_index]}"
    keyboard = [
            [InlineKeyboardButton("Присутствует", callback_data=f"response_{student_index}_1"),
            InlineKeyboardButton("Отсутствует", callback_data=f"response_{student_index}_0")],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=new_text, reply_markup=reply_markup)

async def react_to_photos(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]
    api_dr = GoogleDriveAPI()
    
    photo_file = await photo.get_file()

    filename = f'received_image_{photo_file.file_id}.jpg'
    filename_dir = f'{workdir}/{filename}'
    await photo_file.download_to_drive(filename_dir)
    await context.bot.send_message(text="Спасибо за фото! А еще, пожалуйста, отметьте посещаемость на занятии! Для этого нужно нажать /start", chat_id= update.effective_user.id)
    await api_dr.save_photo(filename)

