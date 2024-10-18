import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
from constants import folder_id, workdir

class GoogleDriveAPI:
# If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
    

    def __init__(self) -> None:
        self.creds = None
        if os.path.exists("token_drive.json"):
            self.creds = Credentials.from_authorized_user_file("token_drive.json", self.SCOPES)
    # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                "credentials_drive.json", self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token_drive.json", "w") as token:
                token.write(self.creds.to_json())
        self.service = build("drive", "v3", credentials=self.creds)


    async def save_photo(self, filename):
        file_metadata = {
                    'name': filename,
                    'parents': [folder_id]
                }
       
        filepath = f"{workdir}/{filename}"
        media = MediaFileUpload(filepath, resumable=True)
        r = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
