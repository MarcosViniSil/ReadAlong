from abc import ABC, abstractmethod

from models.TTSTranscription import TTSTranscription


class TTSProvider(ABC):

    @abstractmethod
    def generate(self, bookTitle: str, texts: list[str]) -> TTSTranscription:
        pass
