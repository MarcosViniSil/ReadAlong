from dataclasses import dataclass
from models.Sentence import Sentence

@dataclass
class Page:
    pageCode: str
    audioFile: str
    Sentence: list[Sentence]
    nextPageCode: str