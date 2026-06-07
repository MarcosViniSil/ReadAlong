from dataclasses import dataclass
from models import SentenceType

@dataclass
class Sentence:
    sentenceType: SentenceType
    pageCode: str
    text: str
    segmentCode: str
    duration: float
    start: float
    end: float
    nextSegmentCode: str