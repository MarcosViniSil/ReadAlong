from abc import ABC, abstractmethod

from models.Book import Book
from models.enum import BookStatus


class BookRepositoryProvider(ABC):

    @abstractmethod
    async def create(self, book: Book):
        pass

    @abstractmethod
    async def get_by_id(self, book_id: str):
        pass

    @abstractmethod
    async def update_status(self, book_id: str, status: BookStatus):
        pass

    @abstractmethod
    async def increment_completed_pages(self, book_id: str):
        pass

    @abstractmethod
    async def get_progress(self, book_id: str):
        pass

