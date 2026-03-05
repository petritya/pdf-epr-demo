import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate(token_file="token.json"):
    """A token.json fájl alapján hitelesít a Google Drive-hoz."""
    with open(token_file, "rb") as f:
        creds = pickle.load(f)

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
