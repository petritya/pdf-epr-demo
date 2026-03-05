from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pandas as pd
import os
import uuid

app = FastAPI()

UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"status": "API működik"}


@app.post("/merge")
async def merge(files: list[UploadFile] = File(...)):

    dfs = []

    for file in files:
        temp_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(temp_path, "wb") as f:
            f.write(await file.read())

        df = pd.read_excel(temp_path)
        dfs.append(df)

        os.remove(temp_path)

    merged = pd.concat(dfs, ignore_index=True)

    output_file = os.path.join(UPLOAD_DIR, f"merged_{uuid.uuid4()}.xlsx")

    merged.to_excel(output_file, index=False)

    return FileResponse(
        output_file,
        filename="egyesitett.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
