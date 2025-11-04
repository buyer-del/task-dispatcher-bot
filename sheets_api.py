from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime

def get_service():
    from config import SERVICE_ACCOUNT_FILE
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()

def append_task(name, description, tag="#інше"):
    from config import SPREADSHEET_ID
    sheet = get_service()

    # Час у зручному текстовому форматі
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_row = [
        "",             # Task ID (порожній — заповнимо пізніше)
        name,           # Назва
        description,    # Опис
        "", "", "", "", "",  # інші поля залишаємо порожніми
        tag,
        "FALSE",
        timestamp,      # Created
        timestamp       # Updated
    ]

    request = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="A:L",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [new_row]}
    )
    response = request.execute()
    return response
