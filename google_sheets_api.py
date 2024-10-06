from datetime import datetime

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from constants import workdir, GOOGLE_SHEET_ATTENDANCE_ID
from google.oauth2 import service_account

class GoogleSheetsAPI:
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # The ID and range of a sample spreadsheet.
    
    RANGE_OF_NAMES = "A:B"

    def __init__(self, id=GOOGLE_SHEET_ATTENDANCE_ID):
        creds = None
        self.SPREADSHEET_ID = id
        if not creds:
            creds = service_account.Credentials.from_service_account_file(f"{workdir}/credentials.json").with_scopes(self.SCOPES)
            if not creds.valid:
                creds.refresh(Request())
            print(creds.valid)
        self.creds = creds

    async def get_list_of_students(self, group_name: str):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.SPREADSHEET_ID, range=f'{group_name}!{self.RANGE_OF_NAMES}')
                .execute()
            )
            students = result.get("values", [])

            if not students:
                print("No data found.")
                return

            return [f'{student[0]} {student[1]}' for student in students[1:]]
        except HttpError as err:
            print(err)

    async def get_timetable(self):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.SPREADSHEET_ID, range=f'Sheet1!A:D')
                .execute()
            )
            students = result.get("values", [])

            if not students:
                print("No data found.")
                return

            return students[1:]
        except HttpError as err:
            print(err)

    async def insert_attendance(self, group_name: str, attendance: list):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            column_to_insert_attendance = await self._get_first_empty_column(group_name)
            attendance_range = f'{group_name}!{column_to_insert_attendance}:{column_to_insert_attendance}'
            attendance_formatted = [[datetime.now().strftime("%d %m")]] + [[str(a)] for a in attendance]
            service.spreadsheets().values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=attendance_range,
                valueInputOption='RAW',
                body={
                    'values': attendance_formatted
                }
            ).execute()
        except HttpError as err:
            print(err)


    async def update_last_attendance(self, group_name: str, attendance: list):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            column_to_insert_attendance = await self._get_last_filled_column(group_name)
            attendance_range = f'{group_name}!{column_to_insert_attendance}:{column_to_insert_attendance}'
            attendance_formatted = [[datetime.now().strftime("%d %m")]] + [[str(a)] for a in attendance]
            service.spreadsheets().values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=attendance_range,
                valueInputOption='RAW',
                body={
                    'values': attendance_formatted
                }
            ).execute()
        except HttpError as err:
            print(err)
            
    async def _index_to_column_letter(self, index):
        letter = ''
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            letter = chr(65 + remainder) + letter  # 65 is the ASCII value for 'A'
        return letter


    async def _get_first_empty_column_index(self, group_name: str):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            # Call the Sheets API
            result = service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=f"{group_name}!1:1"
            ).execute()

            row_values = result.get('values', [])[0] if 'values' in result else []

            return len(row_values) + 1

        except HttpError as err:
            print(err)


    async def _get_first_empty_column(self, group_name: str):
        return await self._index_to_column_letter(await self._get_first_empty_column_index(group_name))

    async def _get_last_filled_column(self, group_name: str):
        return await self._index_to_column_letter(await self._get_first_empty_column_index(group_name) - 1)
