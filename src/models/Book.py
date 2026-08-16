from dataclasses import dataclass
import datetime
from models.enum import BookStatus
from models.enum.languages import Languages

@dataclass
class Book:
    id: str = ""
    title: str = ""
    author: str = ""
    book_url: str
    language: Languages = str(Languages.ENGLISH)
    status: BookStatus
    total_pages: int 
    completed_pages: int
    created_at: datetime
    updated_at: datetime
