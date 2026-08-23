from dataclasses import Field, dataclass
import datetime
from models.enum.BookStatus import BookStatus
from models.enum.languages import Languages

@dataclass
class Book:
    id: str = ""
    title: str = ""
    author: str = ""
    book_url: str = ""
    language: Languages = str(Languages.ENGLISH)
    status: BookStatus = str(BookStatus.PENDING)
    total_pages: int = 0
    completed_pages: int = 0
    created_at: datetime = None
    updated_at: datetime = None
