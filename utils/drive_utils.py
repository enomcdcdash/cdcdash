import io
import os
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import streamlit as st

@st.cache_resource
def get_drive_service():
    credentials_info = st.secrets["gdrive_credentials"]
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=credentials)

def upload_photo_to_drive(file_data, file_name, folder_id):
    service = get_drive_service()
    media = MediaIoBaseUpload(io.BytesIO(file_data), mimetype="image/jpeg")
    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webContentLink, webViewLink"
    ).execute()
    return file.get("id"), file.get("webContentLink")
