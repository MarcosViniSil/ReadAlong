from abc import ABC, abstractmethod

class StorageProvider(ABC):

    @abstractmethod
    def save_audio(self) -> str:
        pass
        