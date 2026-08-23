from dataclasses import dataclass
import datetime
from models.enum import BookStatus

@dataclass
class Page:
    id: str
    processing_run_id: str
    sequence: int
    text: str
    sentence_count: int
    status: BookStatus
    created_at: datetime
    updated_at: datetime