from dataclasses import dataclass
import datetime

from models.enum import BookStatus

@dataclass
class MediaManifest:
    id: str
    book_id: str
    page_id: str
    type: str
    storage_key: str
    status: BookStatus
    created_at: datetime 