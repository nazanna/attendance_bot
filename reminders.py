import logging
import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import pytz
import typing as tp

# Set up logging
logging.basicConfig(level=logging.INFO)

class Reminder():
    def __init__(self, time: str, user_id: str):
        self.time = time
        self.user_id = user_id
        

# Initialize bot with your token
TOKEN = 'YOUR_BOT_TOKEN'

# Schedule data: {time: chat_id}
schedule_data = {
    '13:46': '816623670',
}

# Message to be sent
message = "This is a scheduled message!"

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: str):
    await context.bot.send_message(chat_id=chat_id, text=message)

# async def get_today_reminders() -> tp.List[Reminder]:
#     return [Reminder('13:4', '@andr_zhi')]

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    while True:
        now = datetime.now(pytz.timezone('UTC'))
        
        # if now in schedule_data:
        username = schedule_data['13:46']
        await send_message(context, username)
        # del schedule_data[now]

        round_up = 1
        next_check = now + timedelta(minutes=round_up)
        next_check_time = next_check.replace(second=0, microsecond=0, minute=(next_check.minute // round_up) * round_up)
        print((next_check_time - now).total_seconds())
        await asyncio.sleep(10)
        # await asyncio.sleep((next_check_time - now).total_seconds())  # Check every 10 minutes

def run_scheduler(context: ContextTypes.DEFAULT_TYPE):
    asyncio.run(send_reminders(context))

# async def p():
#     while True:
#         now = datetime.now(pytz.timezone('UTC'))
        
#         # if now in schedule_data:
#         username = schedule_data['13:46']
#         print("pupupu")
#         # del schedule_data[now]
#         round_up = 1
#         next_check = now + timedelta(minutes=round_up)
#         next_check_time = next_check.replace(second=0, microsecond=0, minute=(next_check.minute // round_up) * round_up)

#         await asyncio.sleep((next_check_time - now).total_seconds())  # Check every 10 minutes

# asyncio.run(p())