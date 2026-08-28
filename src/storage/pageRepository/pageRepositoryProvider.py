from abc import ABC, abstractmethod
from typing import Sequence

from models.Book import Book
from models.Page import Page
from models.enum import BookStatus


class PageRepositoryProvider(ABC):

    @abstractmethod
    async def create(self, page: Page):
        pass

    @abstractmethod
    async def get_by_id(self, page_id: int):
        pass

    @abstractmethod
    async def get_by_sequence(self, run_id: int, sequence: Sequence):
        pass

    @abstractmethod
    async def update_status(self, page_id:int, status:BookStatus):
        pass

    @abstractmethod
    async def count_by_status(self, run_id:int, status:BookStatus):
        pass

    @abstractmethod
    async def get_pending_pages(self, run_id:int):
        pass


