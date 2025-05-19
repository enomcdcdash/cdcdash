import io
import base64
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import streamlit as st

@st.cache_resource
def get_drive_service():
    # Decode base64 string from Streamlit secrets
    base64_creds = st.secrets["GOOGLE_DRIVE_CREDS"]
    json_str = base64.b64decode(base64_creds).decode("utf-8")
    credentials_info = json.loads(json_str)

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=credentials)
    return service

def upload_photo_to_drive(file_obj, file_name, folder_id):
    """
    Upload a photo to Google Drive.

    Args:
        file_obj: File-like object (bytes) or Streamlit uploaded file
        file_name: Desired name for the file on Drive
        folder_id: Drive folder ID where the file should be uploaded

    Returns:
        Tuple of (file_id, webContentLink)
    """
    service = get_drive_service()

    # Read bytes from file_obj
    if hasattr(file_obj, "read"):
        file_bytes = file_obj.read()
    else:
        file_bytes = file_obj

    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="image/jpeg")
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
