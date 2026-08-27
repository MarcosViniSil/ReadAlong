from abc import ABC, abstractmethod


class BucketProvider(ABC):

    @abstractmethod
    async def upload(self, key, data):
        pass

    @abstractmethod
    async def download(self, key):
        pass

    @abstractmethod
    async def delete(self, key):
        pass

    @abstractmethod
    async def exists(self, key):
        pass