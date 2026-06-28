from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub
from models.Node import Node
from models.enum.NodeType import NodeType
from parsers.bookParserProvider import BookParser
from parsers.impl.epub.epub_image_extractor import ImageExtractor
from parsers.impl.html_parser import HTMLParser


class EpubParser(BookParser):

    def __init__(self, htmlParser:HTMLParser):
        self.htmlParser = htmlParser

    def extract_text(self, file_path):
        self.__check_file_existence(file_path)

        book = epub.read_epub(file_path)

        image_map = ImageExtractor.extract_images(self, book)

        document = Node(type=NodeType.DOCUMENT)

        for item_id, _ in book.spine:

            item = book.get_item_with_id(item_id)
            if item is None:
                continue

            soup = BeautifulSoup(
                item.get_content(),
                "html.parser"
            )

            body = soup.find("body")

            if body is None:
                continue

            document.children.extend(
                self.htmlParser.parse_children(body, image_map)
            )

        return document

    def __check_file_existence(self, file_path: str) -> None:
        file_path = Path(file_path)

        if not file_path.is_file():
            raise ValueError("The file does not exists")
 