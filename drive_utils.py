import os
import base64
import pickle

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive"]
ENV_TOKEN_B64 = "GOOGLE_TOKEN_JSON"


def authenticate():
    token_b64 = os.environ.get(ENV_TOKEN_B64)
    if not token_b64:
        raise RuntimeError(
            f"Hiányzó környezeti változó: {ENV_TOKEN_B64}. "
            "Railway Settings → Variables alatt add hozzá."
        )

    try:
        token_bytes = base64.b64decode(token_b64)
        creds = pickle.loads(token_bytes)
    except Exception as e:
        raise RuntimeError(
            "Nem sikerült a GOOGLE_TOKEN_JSON Base64/pickle betöltése. "
            "Ellenőrizd, hogy a teljes Base64 string be lett-e másolva."
        ) from e

    # Lejárt token esetén frissítünk (ha van refresh_token)
    try:
        if getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            creds.refresh(Request())
    except Exception as e:
        raise RuntimeError(
            "A Google token frissítése nem sikerült. "
            "Ilyenkor általában újra kell generálni a token-t lokálisan."
        ) from e

    return build("drive", "v3", credentials=creds)


def pdf_to_google_doc(service, pdf_path: str, doc_name: str = "converted_doc") -> str:
    file_metadata = {
        "name": doc_name,
        "mimeType": "application/vnd.google-apps.document",
    }
    media = MediaFileUpload(pdf_path, mimetype="application/pdf")
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    return file.get("id")


def get_doc_text(service, file_id: str) -> str:
    export = (
        service.files()
        .export(fileId=file_id, mimeType="text/plain")
        .execute()
    )
    return export.decode("utf-8")


def delete_file(service, file_id: str) -> None:
    service.files().delete(fileId=file_id).execute()
