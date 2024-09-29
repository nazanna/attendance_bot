import os.path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsAPI:
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # The ID and range of a sample spreadsheet.
    SPREADSHEET_ID = "1E1pBA89XGC1LB3SHVltPuDJeu1odE_BCOxQM_aNcXVs"
    RANGE_OF_NAMES = "A:B"

    def __init__(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        self.creds = creds

    def get_list_of_students(self, group_name: str):
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

    def insert_attendance(self, group_name: str, attendance: list):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            column_to_insert_attendance = self._get_first_empty_column(group_name)
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

    def _get_first_empty_column(self, group_name: str):
        try:
            service = build("sheets", "v4", credentials=self.creds)
            # Call the Sheets API
            result = service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=f"{group_name}!1:1"
            ).execute()

            row_values = result.get('values', [])[0] if 'values' in result else []

            def _index_to_column_letter(index):
                letter = ''
                while index > 0:
                    index, remainder = divmod(index - 1, 26)
                    letter = chr(65 + remainder) + letter  # 65 is the ASCII value for 'A'
                return letter

            return _index_to_column_letter(len(row_values) + 1)

        except HttpError as err:
            print(err)


def main():
    api = GoogleSheetsAPI()
    # print(api.get_list_of_students(class_number=8, group_number=2))
    print(api.insert_attendance("8_2", [1, 1, 0]))


if __name__ == "__main__":
    main()
