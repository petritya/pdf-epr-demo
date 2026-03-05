from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pdfplumber
import pandas as pd
import os
import uuid

app = FastAPI()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"status": "PDF parser működik"}


@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):

    pdf_path = os.path.join(TEMP_DIR, file.filename)

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    os.remove(pdf_path)

    rows = []
    for line in text.split("\n"):
        if ";" in line:
            rows.append(line.split(";"))

    df = pd.DataFrame(rows)

    output_file = os.path.join(TEMP_DIR, f"output_{uuid.uuid4()}.xlsx")

    df.to_excel(output_file, index=False)

    return FileResponse(
        output_file,
        filename="adatok.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
