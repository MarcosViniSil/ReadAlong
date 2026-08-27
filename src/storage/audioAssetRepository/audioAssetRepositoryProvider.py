from abc import ABC, abstractmethod

from models import AudioAsset
from models.Book import Book
from models.enum import BookStatus


class AudioAssetRepositoryProvider(ABC):

    @abstractmethod
    async def create(self, audio_asset: AudioAsset):
        pass

    @abstractmethod
    async def get_by_id(self, audio_asset_id: int):
        pass

    @abstractmethod
    async def get_by_chunk(self, chunk_id:int):
        pass

    @abstractmethod
    async def get_next_job(self):
        pass

    @abstractmethod
    async def get_by_page(self, page_id:int):
        pass

    @abstractmethod
    async def update_status(self, audio_asset_id:int, status: BookStatus):
        pass

