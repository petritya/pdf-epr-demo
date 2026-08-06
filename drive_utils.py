import os
import base64
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive"]
ENV_TOKEN_B64 = "GOOGLE_TOKEN_JSON"


def authenticate():
    creds = None
    token_b64 = os.environ.get(ENV_TOKEN_B64)

    # Railway: token betöltése környezeti változóból
    if token_b64:
        try:
            token_bytes = base64.b64decode(token_b64)
            creds = pickle.loads(token_bytes)
        except Exception as error:
            raise RuntimeError(
                "Nem sikerült a Railway Google-tokenjének betöltése."
            ) from error

    # Helyi futtatás: token betöltése fájlból
    elif os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)

    # Lejárt token frissítése
    if (
        creds
        and getattr(creds, "expired", False)
        and getattr(creds, "refresh_token", None)
    ):
        creds.refresh(Request())

        # Helyben a frissített tokent visszamentjük
        if not token_b64:
            with open("token.json", "wb") as token:
                pickle.dump(creds, token)

    # Helyi új bejelentkezés, ha nincs használható token
    if not creds or not getattr(creds, "valid", False):
        if token_b64:
            raise RuntimeError(
                "A Railway Google-tokenje nem érvényes."
            )

        if not os.path.exists("client_secret.json"):
            raise RuntimeError(
                "Hiányzik a client_secret.json fájl."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            SCOPES,
        )

        creds = flow.run_local_server(port=0)

        with open("token.json", "wb") as token:
            pickle.dump(creds, token)

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
