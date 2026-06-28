from pathlib import Path
from log.loggerService import LoggerService
from models.Element import Element
from models.Node import Node
from models.enum.NodeType import NodeType
from parsers.bookParserProvider import BookParser

class TxtParser(BookParser):

    def extract_text(self, file_path: str) -> str:
        LoggerService.log_info("Starting TXT text extraction for file: %s", file_path)
        self.__check_file_existence(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            content_splitted = content.split("\n")

            LoggerService.log_info("TXT file loaded: %d lines read from '%s'", len(content_splitted), file_path)

            document = Node(type=NodeType.DOCUMENT)
            elements:list[Node] = []

            for row in content_splitted:
                elements.append(Node(NodeType.TEXT,[],row,None))

            document.children.extend(elements)

            LoggerService.log_info("TXT parsing completed for '%s': %d text nodes created", file_path, len(elements))
            return document

    def __check_file_existence(self, file_path: str) -> None:
        file_path = Path(file_path)

        if not file_path.is_file():
            LoggerService.log_error("File not found: %s", file_path)
            raise ValueError("The file does not exists")