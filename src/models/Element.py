from dataclasses import dataclass
from typing import Optional
from models.Page import Page

@dataclass
class Element:
    type: str
    text: Optional[str]
    href: Optional[str]
    src: Optional[str]