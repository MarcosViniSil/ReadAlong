from dataclasses import dataclass
from typing import Optional

@dataclass
class Element:
    type: str
    text: Optional[str]
    href: Optional[str]
    src: Optional[str]

    def __repr__(self):
        preview = (self.text[:60].replace("\n", " ") + "...") if self.text and len(self.text) > 60 else (self.text or "")
        return f"<{self.type}> {preview}"