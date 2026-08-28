from dataclasses import dataclass
import datetime

from models.enum import BookStatus

@dataclass
class AudioAsset:
    id: str
    chunk_id: str
    storage_key: str
    format: str
    duration: float
    size: float
    status: BookStatus
    created_at: datetime    