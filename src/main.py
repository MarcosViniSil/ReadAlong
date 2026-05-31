from fastapi import FastAPI, File, UploadFile
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from pipeline.book_pipeline import BookPipeline


app = FastAPI()
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
async def upload_book(file: UploadFile = File(...)):
    bookPipeline = BookPipeline()
    path = bookPipeline.pipeline(file)
    
    return {"path": str(path)}
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True,lifespan="on")