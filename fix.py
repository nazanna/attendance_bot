import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, \
    ApplicationBuilder

# Define the states for the conversation
WAITING_FOR_MESSAGE = 0

EXPECTED_FORMAT = r'^([а-яА-ЯёЁ]+)\s+([а-яА-ЯёЁ]+)\s+([а-яА-ЯёЁ0-9_]+)\s+(Да|Нет)$'


async def fix(update: Update, context: CallbackContext) -> int:
    """Start the fix command and ask for the user's message."""
    await update.message.reply_text(
        'Введите данные ученика, посещаемость которого вы хотите исправить. \
        Сделайте это в следующем формате: "Фамилия Имя Группа Да/Нет" \
        (в зависимости от того, посетил ученик занятие или нет). Например: Иванов Иван 8_2 Нет. \
        Обратите внимание, что фамилия и имя ученика должны точно совпадать с тем, как они записаны в списке.')
    return WAITING_FOR_MESSAGE


async def check_message(update: Update, context: CallbackContext) -> int:
    """Check the user's message and respond accordingly."""
    user_message = update.message.text

    if re.match(EXPECTED_FORMAT, user_message):
        await update.message.reply_text("Everything alright!")
    else:
        await update.message.reply_text("Please rewrite your message in the expected format.")

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
