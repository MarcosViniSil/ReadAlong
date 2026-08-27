from abc import ABC, abstractmethod

from models.chunk import Chunk
from models.enum import BookStatus


class ChunkRepositoryProvider(ABC):

    @abstractmethod
    async def create(self, chunk: Chunk):
        pass

    @abstractmethod
    async def create_many(self, chunks: list[Chunk]):
        pass

    @abstractmethod
    async def get_by_id(self, chunk_id: int):
        pass

    @abstractmethod
    async def get_by_page(self, page_id:int):
        pass

    @abstractmethod
    async def update_status(self, chunk_id:int, status: BookStatus):
        pass

    @abstractmethod
    async def get_pending(self, page_id:int):
        pass

    @abstractmethod
    async def get_pending_by_run(self, run_id:int):
        pass

    @abstractmethod
    async def count_by_status(self, page_id:int, status: BookStatus):
        pass