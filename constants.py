import os

workdir=os.path.dirname(os.path.abspath(__file__))
DEBUG = 'andrew' in workdir

responses_db_name = f'{workdir}/user_responses{"_test" if DEBUG else ""}.db'
users_db_name = f'{workdir}/user_ids.db'
token_key = f"attendance-bot-{'test' if DEBUG else 'main'}-token"
started = False 

GOOGLE_SHEET_ATTENDANCE_ID = "1z0aV-h_BomCKvBEu3Qne1WtT9StF3LEjWxfayEzcXjk" if not DEBUG else "1TlJBKO3E4bRl7C7Te6l0-XfpvIfDGa6gaj-ebGzPJKE"
GOOGLE_SHEET_REMINDERS_SCHEDULE_ID = "1-y3cE_AIhA8VuRkax-E9-4mSWo4UpnPyxWeFvERHLM4"
folder_id = '13xhsq3KT3RxoB_p2UAspsZ8l09UCUOpw'