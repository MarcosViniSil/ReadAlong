from dataclasses import dataclass
import datetime
from models.enum.BookStatus import BookStatus

@dataclass
class Page:
    id: str = ""
    processing_run_id: str = ""
    sequence: int = 0
    page_url: str = ""
    sentence_count: int = 0
    status: BookStatus = str(BookStatus.PENDING)
    created_at: datetime = None
    updated_at: datetime = None