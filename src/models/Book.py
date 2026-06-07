from dataclasses import dataclass
from models.Page import Page

@dataclass
class Book:
    bookName: str
    bookCode: str
    pages: list[Page]