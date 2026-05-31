from abc import ABC, abstractmethod

class TTSProvider(ABC):

    @abstractmethod
    def generate(self, bookTitle:str,texts: list[str]) -> str:
        pass