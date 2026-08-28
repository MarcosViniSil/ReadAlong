from dataclasses import dataclass
import datetime
from models.enum import BookStatus

@dataclass
class ProcessingRun:
    id: str = ""
    book_id: str = ""
    status: BookStatus = ""
    page_size: int = 0
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
