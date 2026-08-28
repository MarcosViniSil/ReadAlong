from dataclasses import dataclass
import datetime
from models.enum import BookStatus

@dataclass
class Chunk:
    id: str
    page_id: str
    sequence: int
    text: str
    status: BookStatus
    created_at: datetime
    updated_at: datetime
