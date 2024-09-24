import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Укажите области разрешений, которые вам необходимы
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Укажите путь к вашему файлу с секретами сервисного аккаунта
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Создание учетных данных
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)

# Авторизация
gc = gspread.authorize(credentials)

# Теперь вы можете использовать gc для работы с Google Sheets
spreadsheet = gc.open("Списки")
worksheet = spreadsheet.sheet1  # Или укажите конкретный рабочий лист
data = worksheet.get_all_records()  # Получение всех записей

print(data)  # Вывод данных
