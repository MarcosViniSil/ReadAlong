import json
from pathlib import Path
from urllib.parse import quote

import uvicorn
from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from exceptions.register import register_exception_handlers
from pipeline.book_pipeline import BookPipeline
from provider.fileProvider import get_file_storage_service
from provider.ttsProvider import getBookPipelineService
from storage.connection.factory import create_pool
from storage.fileStorageProvider import FileStorageProvider

from contextlib import asynccontextmanager

from fastapi import FastAPI

from storage.connection import Database


AUDIO_DIR = Path("audio")
FRONTEND_DIST = Path("frontend/dist")

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = create_pool()
    db = Database(pool)

    await db.open()

    app.state.db = db

    yield

    await db.close()

app = FastAPI(lifespan=lifespan)


register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/books")
async def upload_book(file: UploadFile = File(...), bookPipeline:BookPipeline = Depends(getBookPipelineService),fileStorageService:FileStorageProvider = Depends(get_file_storage_service),pipeline: BookPipeline = Depends(getBookPipelineService)):
    filePath = fileStorageService.save_file(file)

    return await pipeline.pipeline(filePath)

@app.get("/books")
def list_books():
    if not AUDIO_DIR.exists():
        return []

    books = []
    for json_file in sorted(AUDIO_DIR.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        audio_file = data.get("audioFile", "")
        audio_url = (
            f"/audio/{quote(Path(audio_file).name)}" if audio_file else ""
        )
        books.append({
            "bookCode": data.get("bookCode", json_file.stem),
            "bookName": data.get("bookName", json_file.stem),
            "jsonUrl": f"/audio/{quote(json_file.name)}",
            "audioUrl": audio_url,
            "duration": data.get("duration", 0.0),
            "pages": len(data.get("pages", [])),
        })

    return books


AUDIO_DIR.mkdir(exist_ok=True)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True,lifespan="on")
