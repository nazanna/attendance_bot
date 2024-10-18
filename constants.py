import os

DEBUG = True
workdir=os.path.dirname(os.path.abspath(__file__))

responses_db_name = f'{workdir}/user_responses{"_test" if DEBUG else ""}.db'
users_db_name = f'{workdir}/users{"_test" if DEBUG else ""}.db'
token_key = f"attendance-bot-{'test' if DEBUG else 'main'}-token"
started = False 

GOOGLE_SHEET_ATTENDANCE_ID = "1xmhcDN0bROVfcnCFm2y7-VNnsgjtzhuwcWmMpmGjlK8" if not DEBUG else "1ukMnvZ9tCbtbd_KAv_1hgKAGldRntupD80rFSwwxvSA"
GOOGLE_SHEET_REMINDERS_SCHEDULE_ID = "1-y3cE_AIhA8VuRkax-E9-4mSWo4UpnPyxWeFvERHLM4"
folder_id = '13xhsq3KT3RxoB_p2UAspsZ8l09UCUOpw'