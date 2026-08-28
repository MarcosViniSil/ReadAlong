from abc import ABC, abstractmethod
import uuid
from models import ProcessingRun
from models.enum import BookStatus


class ProcessingRunRepositoryProvider(ABC):

    @abstractmethod
    async def create(self, book_id: uuid, page_size: int = 0) -> ProcessingRun:
        pass

    @abstractmethod
    async def get_by_id(self, run_id: uuid):
        pass

    @abstractmethod
    async def update_status(self, run_id: uuid, status: BookStatus):
        pass

    @abstractmethod
    async def finish(self, run_id:uuid):
        pass


