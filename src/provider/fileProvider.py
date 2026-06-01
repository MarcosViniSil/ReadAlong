from storage.fileStorageProvider import FileStorageProvider
from storage.impl.fileStorageService import FileStorageService

def get_file_storage_service() -> FileStorageProvider:
    return FileStorageService()