from collections import defaultdict

from models.Node import Node
from models.NodeType import NodeType
from models.Element import Element
from parsers.bookParserProvider import BookParser
from pathlib import Path
from sympy import content
from ebooklib import epub, ITEM_IMAGE,ITEM_DOCUMENT
from bs4 import BeautifulSoup,Tag, NavigableString

output_dir = Path("imgs")
output_dir.mkdir(exist_ok=True)

class EpubParser(BookParser):

    def parse_node(self, node, image_map):

        if isinstance(node, NavigableString):
            return None

        if not isinstance(node, Tag):
            return None

        match node.name:

            case "h1" | "h2" | "h3" | "h4" | "h5" | "h6":

                return Node(
                    type=NodeType.HEADING,
                    text=node.get_text(" ", strip=True),
                    metadata={
                        "level": int(node.name[1])
                    }
                )

            case "p":

                paragraph = Node(type=NodeType.PARAGRAPH)

                for child in node.children:

                    parsed = self.parse_node(child, image_map)

                    if parsed:
                        paragraph.children.append(parsed)

                if not paragraph.children:

                    paragraph.text = node.get_text(" ", strip=True)

                return paragraph

            case "img":

                filename = Path(node.get("src", "")).name

                return Node(
                    type=NodeType.IMAGE,
                    metadata={
                        "src": image_map.get(filename)
                    }
                )

            case "blockquote":

                quote = Node(type=NodeType.QUOTE)

                for child in node.children:

                    parsed = self.parse_node(child, image_map)

                    if parsed:
                        quote.children.append(parsed)

                return quote

            case "table":

                table = Node(type=NodeType.TABLE)

                for child in node.children:

                    parsed = self.parse_node(child, image_map)

                    if parsed:
                        table.children.append(parsed)

                return table

            case "tr":

                row = Node(type=NodeType.ROW)

                for child in node.children:

                    parsed = self.parse_node(child, image_map)

                    if parsed:
                        row.children.append(parsed)

                return row

            case "td" | "th":

                cell = Node(type=NodeType.CELL)

                for child in node.children:

                    parsed = self.parse_node(child, image_map)

                    if parsed:
                        cell.children.append(parsed)

                if not cell.children:

                    cell.text = node.get_text(" ", strip=True)

                return cell

            case "code":

                return Node(
                    type=NodeType.CODE,
                    text=node.get_text("\n")
                )

            case "math":

                return Node(
                    type=NodeType.FORMULA,
                    metadata={
                        "raw": str(node)
                    }
                )

            case _:

                # tags como div, span, body...
                container = Node(type=node.name)

                for child in node.children:

                    parsed = self.parse_node(child, image_map)

                    if parsed:
                        container.children.append(parsed)

                if container.children:
                    return container

                return None

    def extract_text(self, file_path):

        book = epub.read_epub(file_path)

        image_map = self.extract_images(file_path)

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

            for child in body.children:

                parsed = self.parse_node(child, image_map)

                if parsed:
                    document.children.append(parsed)

        return document

    def extract_images(self,file_path:Path) -> dict:
        book = epub.read_epub(file_path)
        image_map = {}
  
        for img in book.get_items_of_type(ITEM_IMAGE):
            local_path = output_dir / Path(img.file_name).name

            if not local_path:
                continue

            with open(local_path, "wb") as f:
                f.write(img.get_content())

            image_map[Path(img.file_name).name] = str(local_path)

        return image_map