import os

DEBUG = True
workdir=os.path.dirname(os.path.abspath(__file__))

responses_db_name = f'{workdir}/user_responses{"_test" if DEBUG else ""}.db'
users_db_name = f'{workdir}/users{"_test" if DEBUG else ""}.db'
token_key = f"attendance-bot-{'test' if DEBUG else 'main'}-token"
started = False 

GOOGLE_SHEET_ATTENDANCE_ID = "1TlJBKO3E4bRl7C7Te6l0-XfpvIfDGa6gaj-ebGzPJKE" if not DEBUG else "1TlJBKO3E4bRl7C7Te6l0-XfpvIfDGa6gaj-ebGzPJKE"
GOOGLE_SHEET_REMINDERS_SCHEDULE_ID = "1-y3cE_AIhA8VuRkax-E9-4mSWo4UpnPyxWeFvERHLM4"
folder_id = '13xhsq3KT3RxoB_p2UAspsZ8l09UCUOpw'