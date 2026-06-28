from pathlib import Path

from models.Element import Element
from models.Node import Node
from models.NodeType import NodeType
from parsers.bookParserProvider import BookParser

class TxtParser(BookParser):

    def extract_text(self, file_path: str) -> str:
        self.__check_file_existence(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            content_splitted = content.split("\n")
            
            document = Node(type=NodeType.DOCUMENT)
            elements:list[Node] = []

            for row in content_splitted:
                elements.append(Node(NodeType.TEXT,[],row,None))

            document.children.extend(elements)

            return document
    
    def __check_file_existence(self, file_path: str) -> None:
        file_path = Path(file_path)

        if not file_path.is_file():
            raise ValueError("The file does not exists")