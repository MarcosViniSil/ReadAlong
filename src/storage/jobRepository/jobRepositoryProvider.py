from abc import ABC, abstractmethod

from models.chunk import Chunk
from models.enum import BookStatus


class JobRepositoryProvider(ABC):

    @abstractmethod
    async def create(self, chunk_id: int):
        pass

    @abstractmethod
    async def create_many(self, chunk_ids: list[int]):
        pass

    @abstractmethod
    async def get_by_id(self, chunk_id: int):
        pass

    @abstractmethod
    async def claim(self, job_id:int, worker_id: int):
        pass

    @abstractmethod
    async def mark_processing(self, job_id: int):
        pass

    @abstractmethod
    async def mark_completed(self, job_id:int):
        pass

    @abstractmethod
    async def mark_failed(self, job_id:int):
        pass

    @abstractmethod
    async def increment_attempt(self, job_id:int):
        pass

    @abstractmethod
    async def get_pending(self):
        pass

    @abstractmethod
    async def get_stale_jobs(self):
        pass