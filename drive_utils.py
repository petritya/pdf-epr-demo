import os, base64, pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    token_b64 = os.environ["GOOGLE_TOKEN_JSON"]
    token_bytes = base64.b64decode(token_b64)
    creds = pickle.loads(token_bytes)
    service = build("drive", "v3", credentials=creds)
    return service

def pdf_to_google_doc(service, pdf_path, doc_name="converted_doc"):
    file_metadata = {
        "name": doc_name,
        "mimeType": "application/vnd.google-apps.document"
    }
    media = MediaFileUpload(pdf_path, mimetype="application/pdf")
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    return file.get("id")

def get_doc_text(service, file_id):
    export = service.files().export(
        fileId=file_id,
        mimeType="text/plain"
    ).execute()
    return export.decode("utf-8")
