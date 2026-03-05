from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import os
import uuid
from parser import parse_text
from drive_utils import authenticate, pdf_to_google_doc, get_doc_text
from openpyxl import Workbook

app = FastAPI()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "PDF parser működik"}

@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    # PDF mentése lokálisan
    pdf_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # Google Drive hitelesítés
    

    # PDF → Google Docs → TXT
    doc_id = pdf_to_google_doc(service, pdf_path, doc_name=file.filename)
    text = get_doc_text(service, doc_id)

    # TXT feldolgozás a parserrel
    data = parse_text(text)

    # Excel mentés
    output_file = os.path.join(TEMP_DIR, f"output_{uuid.uuid4()}.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "Termékek"
    ws.append(["Nev", "Cikkszam", "Brutto_suly"])
    for row in data:
        ws.append(row)
    wb.save(output_file)

    # Lokális PDF törlése
    os.remove(pdf_path)

    return FileResponse(
        output_file,
        filename="adatok.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
