from dataclasses import dataclass
import datetime
from models.enum import BookStatus

@dataclass
class ProcessingRun:
    id: str = ""
    book_id: str = ""
    status: BookStatus = ""
    page_size: int
    created_at: datetime
    started_at: datetime
    completed_at: datetime
