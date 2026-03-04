from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
import io
import csv

from parser import parse_text

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Lengyel számla → EPR CSV demo</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit">Feltöltés</button>
    </form>
    """

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    data = parse_text(text)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Nev", "Cikkszam", "Brutto_suly"])
    writer.writerows(data)

    output.seek(0)

    csv_content = output.getvalue().encode("utf-8-sig")

    return StreamingResponse(
        io.BytesIO(csv_content),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=output.csv"}
    )
