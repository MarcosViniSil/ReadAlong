from dataclasses import dataclass, field
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
    block_type: str = ""
    block_code: str = ""
    metadata: dict = field(default_factory=dict)