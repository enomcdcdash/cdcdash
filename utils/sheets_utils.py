import json
import base64
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st

# ---- Authenticate and Build Sheets API ----
@st.cache_resource
def get_sheets_service():
    base64_creds = st.secrets["GOOGLE_DRIVE_CREDS"]
    json_str = base64.b64decode(base64_creds).decode("utf-8")
    credentials_info = json.loads(json_str)

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=credentials)

# ---- Read data from Sheet and return as DataFrame ----
def read_sheet(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    service = get_sheets_service()
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=f"{sheet_name}")
            .execute()
        )
        values = result.get("values", [])
        if not values:
            return pd.DataFrame()
        headers, *rows = values
        return pd.DataFrame(rows, columns=headers)
    except HttpError as err:
        st.error(f"Gagal membaca data dari Google Sheet: {err}")
        return pd.DataFrame()

# ---- Append new data to Sheet ----
def append_to_sheet(sheet_id: str, sheet_name: str, new_row: dict):
    service = get_sheets_service()
    values = [list(new_row.values())]
    try:
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=sheet_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        ).execute()
    except HttpError as err:
        st.error(f"Gagal menambahkan data ke Google Sheet: {err}")
