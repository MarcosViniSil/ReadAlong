from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import UploadFile

class FileStorageProvider(ABC):

    @abstractmethod
    def save_file(self,file: UploadFile) -> Path:
        pass

        