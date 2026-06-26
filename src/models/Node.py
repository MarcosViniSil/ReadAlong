from dataclasses import dataclass, field
from models import NodeType


@dataclass
class Node:
    type: NodeType
    children: list["Node"] = field(default_factory=list)
    text: str = field(default_factory=str)
    metadata: dict = field(default_factory=dict)