import os.path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from constants import workdir

class GoogleSheetsAPI:
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # The ID and range of a sample spreadsheet.
    
    RANGE_OF_NAMES = "A:B"

    def __init__(self, id="1xmhcDN0bROVfcnCFm2y7-VNnsgjtzhuwcWmMpmGjlK8"):
        creds = None
        self.SPREADSHEET_ID = id
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(f"{workdir}/token.json"):
            creds = Credentials.from_authorized_user_file(f"{workdir}/token.json", self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    f"{workdir}/credentials.json", self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(f"{workdir}/token.json", "w") as token:
                token.write(creds.to_json())
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
                valueInputOption='RAW',  # or 'USER_ENTERED'
                body={
                    'values': attendance_formatted
                }
            ).execute()
        except HttpError as err:
            print(err)


    async def update_last_attendance(self, sheet_name: str, index: int, new_value: int):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            column_to_insert_attendance = await self._get_last_filled_column(sheet_name)
            service.spreadsheets().values().update(
                spreadsheetId=self.SPREADSHEET_ID,
                range=f'{sheet_name}!{column_to_insert_attendance}{index}',
                valueInputOption='RAW',  # or 'USER_ENTERED'
                body={
                    'values': [[new_value]]
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

# def main():
#     api = GoogleSheetsAPI()
#     # print(api.get_list_of_students(class_number=8, group_number=2))
#     print(api.insert_attendance("8_2", [1, 1, 0]))


# if __name__ == "__main__":
#     main()
