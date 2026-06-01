from fastapi import Depends, FastAPI, File, UploadFile
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from exceptions.register import register_exception_handlers
from pipeline.book_pipeline import BookPipeline
from provider.fileProvider import get_file_storage_service
from provider.ttsProvider import getBookPipelineService
from storage.fileStorageProvider import FileStorageProvider


app = FastAPI()

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
async def upload_book(file: UploadFile = File(...), bookPipeline:BookPipeline = Depends(getBookPipelineService),fileStorageService:FileStorageProvider = Depends(get_file_storage_service)):
    filePath = fileStorageService.save_file(file)
    
    return bookPipeline.pipeline(filePath)
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True,lifespan="on")