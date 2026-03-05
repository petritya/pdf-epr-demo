from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
import pdfplumber
import io
import csv

from parser import parse_text

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Lengyel számla → EPR CSV demo</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".pdf">
        <button type="submit">PDF feltöltése</button>
    </form>
    """


@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    # PDF beolvasása
    content = await file.read()

    text = ""

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # Parser feldolgozza
    data = parse_text(text)

    # CSV készítés
    output = io.StringIO()

    # Excel kompatibilis BOM
    output.write("\ufeff")

    writer = csv.writer(output, delimiter=";")

    writer.writerow(["Nev", "Cikkszam", "Brutto_suly"])

    for row in data:
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=output.csv"},
    )
