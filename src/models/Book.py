from dataclasses import dataclass
from src.models.Segment import Segment

@dataclass
class Book:
    id: str
    title: str
    segments: list[Segment]