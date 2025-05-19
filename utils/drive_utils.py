import io
import base64
import json
from typing import Tuple, Union
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

    st.write("Length of base64 string:", len(base64_creds))
    st.write("Decoded JSON preview:", json_str[:200])  # print first 200 chars
    st.write("Credentials JSON keys:", list(credentials_info.keys()))
    
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=credentials)
    return service

def upload_photo_to_drive(
    file_obj: Union[io.BytesIO, bytes],
    file_name: str,
    folder_id: str
) -> Tuple[str, str]:
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

    # 👇 Make the file publicly viewable
    service.permissions().create(
        fileId=file.get("id"),
        body={
            "type": "anyone",
            "role": "reader"
        }
    ).execute()

    return file.get("id"), file.get("webContentLink")

def get_photo_download_link(file_id: str) -> str:
    """
    Generate a direct download/view link for a Google Drive file ID.
    """
    return f"https://drive.google.com/uc?id={file_id}&export=download"
