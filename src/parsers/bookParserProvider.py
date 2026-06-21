from abc import ABC, abstractmethod

class BookParser(ABC):

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        pass