# utils/sheets_utils.py
import base64
import json
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def get_gspread_client():
    # Decode base64 string from Streamlit secrets
    base64_creds = st.secrets["GOOGLE_DRIVE_CREDS"]
    json_str = base64.b64decode(base64_creds).decode("utf-8")
    credentials_info = json.loads(json_str)

    credentials = Credentials.from_service_account_info(
        credentials_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(credentials)
    return client

def append_row_to_sheet(sheet_id, worksheet_name, row_data):
    sh = client.open_by_key(sheet_id)
    worksheet = sh.worksheet(worksheet_name)

    # Ensure row_data matches header order
    if isinstance(row_data, dict):
        header = worksheet.row_values(1)  # ['site_id', 'tanggal_pengisian', ...]
        row_data = [row_data.get(col, "") for col in header]  # Ordered list

    worksheet.append_row(row_data, value_input_option="USER_ENTERED")

def read_sheet_as_dataframe(sheet_id: str, worksheet_name: str) -> pd.DataFrame:
    client = get_gspread_client()
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)
