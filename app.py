from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
import io
import csv
import os
import json

from parser import parse_text

# Google imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = FastAPI()

# ---------- GOOGLE AUTH SETUP ----------

SCOPES = ['https://www.googleapis.com/auth/drive']

service_account_info = json.loads(
    os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
)

credentials = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=SCOPES
)

drive_service = build('drive', 'v3', credentials=credentials)


# ---------- FRONTEND ----------

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Lengyel számla → EPR CSV demo</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit">Feltöltés</button>
    </form>
    """


# ---------- UPLOAD ENDPOINT ----------

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    content = await file.read()

    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Csak PDF fájl tölthető fel"}

    # 1️⃣ Feltöltés + konvertálás Google Docs-ra
    file_metadata = {
        'name': 'uploaded.pdf',
        'mimeType': 'application/vnd.google-apps.document'
    }

    media = MediaIoBaseUpload(
        io.BytesIO(content),
        mimetype='application/pdf'
    )

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')

    # 2️⃣ Export TXT-be
    text = drive_service.files().export(
        fileId=file_id,
        mimeType='text/plain'
    ).execute().decode("utf-8")

    # 3️⃣ Törlés Drive-ról
    drive_service.files().delete(fileId=file_id).execute()

    # 4️⃣ Saját parser
    data = parse_text(text)

    # 5️⃣ CSV generálás
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Nev", "Cikkszam", "Brutto_suly"])
    writer.writerows(data)

    csv_content = output.getvalue().encode("utf-8-sig")

    return StreamingResponse(
        io.BytesIO(csv_content),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=output.csv"}
    )
