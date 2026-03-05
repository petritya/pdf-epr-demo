from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse

import io
from openpyxl import Workbook
import os
import json
from google.oauth2 import service_account

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from parser import parse_text


app = FastAPI()


# -------------------------
# Google Drive kapcsolat
# -------------------------

service_account_info = json.loads(
    os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
)

credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/drive"]
)

drive_service = build("drive", "v3", credentials=credentials)


# -------------------------
# Weboldal
# -------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>PDF → EPR Excel demo</h2>

    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit">Feltöltés</button>
    </form>
    """


# -------------------------
# PDF feldolgozás
# -------------------------

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    content = await file.read()

    pdf_stream = io.BytesIO(content)

    file_metadata = {
        "name": "temp_doc",
        "mimeType": "application/vnd.google-apps.document"
    }

    media = MediaIoBaseUpload(pdf_stream, mimetype="application/pdf")

    created_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = created_file["id"]


    # -------------------------
    # DOC → TXT
    # -------------------------

    text_bytes = drive_service.files().export(
        fileId=file_id,
        mimeType="text/plain"
    ).execute()

    text = text_bytes.decode("utf-8")


    # -------------------------
    # Google doc törlése
    # -------------------------

    drive_service.files().delete(fileId=file_id).execute()


    # -------------------------
    # parser
    # -------------------------

    data = parse_text(text)


    # -------------------------
    # Excel generálás
    # -------------------------

    wb = Workbook()
    ws = wb.active

    ws.append(["Nev", "Cikkszam", "Brutto_suly"])

    for row in data:
        ws.append(row)

    output = io.BytesIO()
    wb.save(output)

    output.seek(0)


    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=output.xlsx"}
    )
