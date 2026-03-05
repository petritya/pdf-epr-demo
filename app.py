import io
import os
import pandas as pd

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# =========================
# Google API hitelesítés
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents.readonly"
]

SERVICE_ACCOUNT_FILE = "service_account.json"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=credentials)
docs_service = build("docs", "v1", credentials=credentials)


# =========================
# PDF → Google Docs
# =========================

def pdf_to_google_doc(pdf_path):

    file_metadata = {
        "name": "converted_doc",
        "mimeType": "application/vnd.google-apps.document"
    }

    media = MediaFileUpload(
        pdf_path,
        mimetype="application/pdf"
    )

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return file.get("id")


# =========================
# Google Docs → szöveg
# =========================

def read_google_doc(doc_id):

    doc = docs_service.documents().get(documentId=doc_id).execute()

    text = ""

    for content in doc.get("body").get("content"):
        paragraph = content.get("paragraph")

        if paragraph:
            for element in paragraph.get("elements"):
                text_run = element.get("textRun")

                if text_run:
                    text += text_run.get("content")

    return text


# =========================
# szöveg → Excel
# =========================

def text_to_excel(text):

    lines = text.split("\n")

    data = []

    for line in lines:

        if line.strip() == "":
            continue

        parts = line.split()

        data.append({
            "sor": line,
            "szavak_szama": len(parts)
        })

    df = pd.DataFrame(data)

    df.to_excel("eredmeny.xlsx", index=False)


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    pdf_file = "input.pdf"

    print("PDF feltöltése...")

    doc_id = pdf_to_google_doc(pdf_file)

    print("Szöveg kiolvasása...")

    text = read_google_doc(doc_id)

    print("Excel generálása...")

    text_to_excel(text)

    print("Kész: eredmeny.xlsx")
