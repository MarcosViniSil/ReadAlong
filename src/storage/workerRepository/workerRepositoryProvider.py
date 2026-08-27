from abc import ABC, abstractmethod

from models import WorkerMetric
from models.Book import Book
from models.enum import BookStatus, WorkerStatus
from models.worker import Worker


class WorkerRepositoryProvider(ABC):

    @abstractmethod
    async def register(self, worker: Worker):
        pass

    @abstractmethod
    async def get_by_id(self, worker_id: int):
        pass

    @abstractmethod
    async def get_all(self):
        pass

    @abstractmethod
    async def update_status(self, worker_id: int, status: WorkerStatus):
        pass

    @abstractmethod
    async def heartbeat(self, worker_id:int):
        pass

    @abstractmethod
    async def update_metrics(self, metrics:WorkerMetric):
        pass

    @abstractmethod
    async def get_online_workers(self):
        pass


