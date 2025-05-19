import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import streamlit as st
import mimetypes

@st.cache_resource
def get_drive_service():
    credentials_info = st.secrets["gdrive_credentials"]
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=credentials)

def upload_photo_to_drive(file_data: bytes, file_name: str, folder_id: str = None):
    service = get_drive_service()
    mime_type, _ = mimetypes.guess_type(file_name)
    if mime_type is None:
        mime_type = "application/octet-stream"  # fallback
    
    media = MediaIoBaseUpload(io.BytesIO(file_data), mimetype=mime_type)
    file_metadata = {"name": file_name}
    if folder_id:
        file_metadata["parents"] = [folder_id]
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webContentLink, webViewLink"
    ).execute()
    return file.get("id"), file.get("webContentLink")

def get_photo_download_link(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"
