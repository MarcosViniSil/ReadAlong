from dataclasses import dataclass

@dataclass
class Segment:
    id: str
    text: str
    audio_file: str | None = None