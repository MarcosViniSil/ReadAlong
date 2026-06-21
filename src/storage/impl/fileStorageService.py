from pathlib import Path
import shutil
from fastapi import UploadFile
from exceptions.PipelineException import FileStorageError
from log.loggerService import LoggerService
from storage.fileStorageProvider import FileStorageProvider

UPLOAD_DIR = Path("./temp")

class FileStorageService(FileStorageProvider):
    
    def save_file(self,file: UploadFile) -> Path:
        try:
            LoggerService.log_info(f"FileStorageService - saving file locally by name {file.filename}")
            UPLOAD_DIR.mkdir(exist_ok=True)

            file_path = UPLOAD_DIR / file.filename

            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            LoggerService.log_info(f"FileStorageService - file {file.filename} saved on {file_path}")
            return file_path
        except Exception as e:
            LoggerService.log_exception(
                "FileStorageService - Error when trying to save file locally %s",
                file_path
            )
            raise FileStorageError("An error occurred when trying to save file locally")