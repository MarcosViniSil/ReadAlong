from pathlib import Path
from bs4 import BeautifulSoup
from ebooklib import epub
from log.loggerService import LoggerService
from models.Node import Node
from models.enum.NodeType import NodeType
from parsers.bookParserProvider import BookParser
from parsers.impl.epub.epub_image_extractor import ImageExtractor
from parsers.impl.html_parser import HTMLParser

class EpubParser(BookParser):

    def __init__(self, htmlParser:HTMLParser):
        self.htmlParser = htmlParser
        LoggerService.log_info("EpubParser initialized")

    def extract_text(self, file_path):
        LoggerService.log_info("Starting EPUB text extraction for file: %s", file_path)
        self.__check_file_existence(file_path)

        book = epub.read_epub(file_path)
        LoggerService.log_info("EPUB file loaded successfully: %s", file_path)

        image_map = ImageExtractor.extract_images(book)
        LoggerService.log_info("Extracted %d images from EPUB", len(image_map))

        document = Node(type=NodeType.DOCUMENT)
        spine_items_processed = 0

        for item_id, _ in book.spine:

            item = book.get_item_with_id(item_id)
            if item is None:
                LoggerService.log_warning("Spine item with id '%s' not found in EPUB; skipping", item_id)
                continue

            soup = BeautifulSoup(
                item.get_content(),
                "html.parser"
            )

            body = soup.find("body")

            if body is None:
                LoggerService.log_warning("No <body> tag found in spine item '%s'; skipping", item_id)
                continue

            document.children.extend(
                self.htmlParser.parse_children(body, image_map)
            )
            spine_items_processed += 1

        LoggerService.log_info(
            "EPUB parsing completed for '%s': %d spine items processed, %d document nodes created",
            file_path, spine_items_processed, len(document.children)
        )
        return document

    def __check_file_existence(self, file_path: str) -> None:
        file_path = Path(file_path)

        if not file_path.is_file():
            LoggerService.log_error("File not found: %s", file_path)
            raise ValueError("The file does not exists")
 