"""Single-worker, bounded pilot. Documents and results are kept only in memory."""
import asyncio
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from converter import collect_pdfs, split_pages, convert, MAX_BYTES

jobs = {}
lock = asyncio.Lock()
tasks = set()
TTL = 900

def ready():
    return bool(os.getenv('OPENAI_API_KEY') and os.getenv('PRIVACY_URL'))

async def cleanup():
    while True:
        await asyncio.sleep(30)
        now = time.monotonic()
        for key in list(jobs):
            if jobs[key]['state'] in ('done', 'error') and now - jobs[key]['updated'] > TTL:
                del jobs[key]

@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(cleanup())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.middleware('http')
async def headers(request, call_next):
    # Browser sends Content-Length for FormData. Reject before multipart parsing.
    if request.method == 'POST':
        try:
            size = int(request.headers.get('content-length', '0'))
        except ValueError:
            return Response(status_code=400)
        if size <= 0 or size > MAX_BYTES + 1024 * 1024:
            return Response('Túl nagy vagy ismeretlen méretű feltöltés.', status_code=413)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

@app.get('/', response_class=HTMLResponse)
def home():
    return Path(__file__).with_name('index.html').read_text()

@app.get('/config')
def config():
    return {'version': '2026-09-28-combined-v5', 'ready': ready(), 'privacy_url': os.getenv('PRIVACY_URL', '')}

async def run_job(token, documents):
    try:
        def progress(done, total):
            jobs[token].update(done=done, total=total)
        name, data, mime = await asyncio.to_thread(convert, documents, progress=progress)
        jobs[token].update(state='done', filename=name, data=data, mime=mime, updated=time.monotonic())
    except Exception:
        # Never log customer data, API responses, or filenames.
        jobs[token].update(state='error', message='Nem sikerült teljes eredményt készíteni. Próbáld kisebb adaggal vagy olvashatóbb PDF-fel.', updated=time.monotonic())

@app.post('/jobs', status_code=202)
async def submit(request: Request):
    if not ready():
        raise HTTPException(503, 'A próba még nincs megnyitva.')
    async with lock:
        # Fixed global per-process quota, not a claim of per-person entitlement.
        if len(jobs) >= 20 or any(j['state'] == 'running' for j in jobs.values()):
            raise HTTPException(429, 'A feldolgozó foglalt. Kérlek, próbáld később.')
        if app.state.used >= int(os.getenv('PILOT_MAX_JOBS', '20')):
            raise HTTPException(429, 'A tesztüzem feldolgozási kerete elfogyott.')
        async with request.form(max_files=5, max_fields=2, max_part_size=MAX_BYTES) as form:
            if form.get('consent') != 'yes':
                raise HTTPException(400, 'Ismerd meg az adatkezelési tájékoztatót.')
            inputs = []
            total = 0
            for item in form.getlist('files'):
                if not hasattr(item, 'read'):
                    raise HTTPException(400, 'Hibás fájlmező.')
                data = await item.read(MAX_BYTES + 1)
                total += len(data)
                if total > MAX_BYTES:
                    raise HTTPException(413, 'Összesen legfeljebb 20 MB tölthető fel.')
                inputs.append((item.filename or '', data))
        try:
            documents = await asyncio.to_thread(lambda: split_pages(collect_pdfs(inputs)))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        token = secrets.token_urlsafe(32)
        jobs[token] = {'state': 'running', 'done': 0, 'total': sum(len(p) for _, p in documents), 'updated': time.monotonic()}
        app.state.used += 1
        task = asyncio.create_task(run_job(token, documents))
        tasks.add(task)
        task.add_done_callback(tasks.discard)
        return {'id': token}

app.state.used = 0

@app.get('/jobs/{token}')
def status(token: str):
    job = jobs.get(token)
    if not job:
        raise HTTPException(404, 'A feladat lejárt vagy nem található.')
    return {key: value for key, value in job.items() if key in ('state', 'done', 'total', 'message', 'filename')}

@app.get('/jobs/{token}/download')
def download(token: str):
    job = jobs.get(token)
    if not job or job['state'] != 'done':
        raise HTTPException(404, 'A letöltés nem elérhető.')
    from urllib.parse import quote
    return Response(job['data'], media_type=job['mime'], headers={'Content-Disposition': "attachment; filename*=UTF-8''" + quote(job['filename'])})
