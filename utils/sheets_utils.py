import base64
import json
from typing import List
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

@st.cache_resource
def get_gsheet_client():
    """
    Authenticate and return a gspread client using base64-encoded service account JSON from Streamlit secrets.
    """
    base64_creds = st.secrets["GOOGLE_DRIVE_CREDS"]
    json_str = base64.b64decode(base64_creds).decode("utf-8")
    credentials_info = json.loads(json_str)

    creds = Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def append_row_to_sheet(
    spreadsheet_name: str,
    worksheet_name: str,
    row_data: List
):
    """
    Append a row of data to a worksheet in the given Google Sheet.

    Args:
        spreadsheet_name (str): Name of the Google Sheet (must be shared with service account).
        worksheet_name (str): Name of the worksheet/tab inside the sheet.
        row_data (List): List of values to append as a row.
    """
    client = get_gsheet_client()
    sheet = client.open(spreadsheet_name)
    worksheet = sheet.worksheet(worksheet_name)
    worksheet.append_row(row_data, value_input_option="USER_ENTERED")
