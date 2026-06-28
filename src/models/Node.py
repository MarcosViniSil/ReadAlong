from dataclasses import dataclass, field
from models.enum.NodeType import NodeType


@dataclass
class Node:
    type: NodeType
    children: list["Node"] = field(default_factory=list)
    text: str = field(default_factory=str)
    metadata: dict = field(default_factory=dict)

    def __str__(self):
        lines = []
        self._format_tree(lines, "", True)
        return "\n".join(lines)

    def _format_tree(self, lines, prefix, is_last):
        label = self.type.value if isinstance(self.type, NodeType) else str(self.type)

        if self.text:
            preview = self.text[:80].replace("\n", " ")
            if len(self.text) > 80:
                preview += "..."
            label += f": {preview}"
        elif self.type == NodeType.IMAGE and self.metadata.get("src"):
            label += f": {self.metadata['src']}"
        elif self.type == NodeType.FORMULA and self.metadata.get("raw"):
            raw = self.metadata["raw"][:60]
            label += f": {raw}"

        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{label}")

        child_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(self.children):
            child._format_tree(lines, child_prefix, i == len(self.children) - 1)

    def linearize(self):
        output = []
    
        self._linearize(output)
    
        return output
    
    
    def _linearize(self, output):
        if self.text:
            
            output.append(
                f"{self.type}: {self.text}"
            )
    
        elif self.type == NodeType.IMAGE:
            output.append(
                f"IMAGE -> {self.metadata.get('src')}"
            )
    
        elif self.type == NodeType.HEADING:
            output.append(
                f"HEADING(level={self.metadata.get('level')})"
            )
    
        for child in self.children:
            child._linearize(output)