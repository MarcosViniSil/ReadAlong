from abc import ABC, abstractmethod

class StorageTTSProvider(ABC):

    @abstractmethod
    def save_audio(self) -> str:
        pass