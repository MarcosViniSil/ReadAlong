from abc import ABC, abstractmethod

from models.Book import Book
from models.enum import BookStatus


class ProcessingRunRepositoryProvider(ABC):

    @abstractmethod
    async def create(self, book_id: int):
        pass

    @abstractmethod
    async def get_by_id(self, run_id: int):
        pass

    @abstractmethod
    async def update_status(self, run_id: int, status: BookStatus):
        pass

    @abstractmethod
    async def finish(self, run_id:int):
        pass


