from fastapi import File, UploadFile
from pathlib import Path
import shutil

from parsers import parserFactory
from processing.sentence_splitter import Splitter
from tts.imp.TTSProviderImpl import KokoroProviderImpl

UPLOAD_DIR = Path("./temp")

class BookPipeline():
    
    def __init__(self):
        pass
    
    def saveFileLocally(self,file: UploadFile = File(...)) -> str:
        UPLOAD_DIR.mkdir(exist_ok=True)

        file_path = UPLOAD_DIR / file.filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return file_path
    
    def pipeline(self,file: UploadFile = File(...)) -> None:
        file_path = self.saveFileLocally(file)
        print(file_path)
        parser = parserFactory.ParserFactory().create(file_path)
        content = parser.extract_text(file_path)
        print(content)
        splitter = Splitter()
        phrases = splitter.split_into_chunks(content)
        print(phrases)
        audio = KokoroProviderImpl()
        audio.generate("test",phrases)
        return file_path