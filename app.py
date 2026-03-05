import os
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from openpyxl import Workbook

from parser import parse_text
from drive_utils import (
    authenticate,
    pdf_to_google_doc,
    get_doc_text,
    delete_file,
)

app = FastAPI()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"status": "PDF → Google Docs → TXT → Excel parser működik"}


@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Csak PDF fájl tölthető fel.")

    # 1) PDF mentése ideiglenesen
    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    pdf_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{safe_name}")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Üres fájl érkezett.")

        with open(pdf_path, "wb") as f:
            f.write(content)

        # 2) Drive auth (Railway env var-ból)
        service = authenticate()

        # 3) PDF → Google Doc
        doc_id = pdf_to_google_doc(service, pdf_path, doc_name=safe_name)

        try:
            # 4) Google Doc → TXT
            text = get_doc_text(service, doc_id)

            # 5) TXT → adatok (a TE meglévő regex parsered)
            data = parse_text(text)

            # 6) Excel generálás
            output_file = os.path.join(TEMP_DIR, f"output_{uuid.uuid4()}.xlsx")

            wb = Workbook()
            ws = wb.active
            ws.title = "Termékek"
            ws.append(["Nev", "Cikkszam", "Brutto_suly"])

            for row in data:
                ws.append(list(row))

            wb.save(output_file)

            # 7) Excel vissza a usernek
            return FileResponse(
                output_file,
                filename="adatok.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        finally:
            # Google Doc törlése, ne teljen be a Drive-od “converted_doc”-okkal
            try:
                delete_file(service, doc_id)
            except Exception:
                # nem kritikus, csak logban látszódhat majd
                pass

    finally:
        # Lokális temp PDF törlése
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception:
            pass
