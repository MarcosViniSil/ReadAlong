from abc import ABC, abstractmethod
from pathlib import Path

class FileTypeDetection(ABC):

    @abstractmethod
    def detect_extension(file_path: Path) -> str:
        pass