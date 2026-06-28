from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from ebooklib import ITEM_IMAGE, epub
from mathml_to_latex.converter import MathMLToLaTeX
from models.Node import Node
from models.NodeType import NodeType
from parsers.bookParserProvider import BookParser


output_dir = Path("imgs")
output_dir.mkdir(exist_ok=True)


class EpubParser(BookParser):

    # -------------------------
    # Utilidades
    # -------------------------

    def parse_children(self, parent, image_map):
        result = []

        for child in parent.children:
            result.extend(self.parse_node(child, image_map))

        return result

    def text_node(self, text):
        text = " ".join(str(text).split())

        if not text:
            return []

        return [
            Node(
                type=NodeType.TEXT,
                text=text
            )
        ]

    # -------------------------
    # Parser
    # -------------------------

    def parse_node(self, node, image_map):

        # texto
        if isinstance(node, NavigableString):
            return self.text_node(node)

        if not isinstance(node, Tag):
            return []
        print("node.name ", node.name)
        match node.name:
            # --------------------
            # Headings
            # --------------------

            case "h1" | "h2" | "h3" | "h4" | "h5" | "h6":

                return [
                    Node(
                        type=NodeType.HEADING,
                        metadata={
                            "level": int(node.name[1])
                        },
                        children=self.parse_children(node, image_map)
                    )
                ]

            # --------------------
            # Paragraph
            # --------------------

            case "p":

                return [
                    Node(
                        type=NodeType.PARAGRAPH,
                        children=self.parse_children(node, image_map)
                    )
                ]

            # --------------------
            # Blockquote
            # --------------------

            case "blockquote":

                return [
                    Node(
                        type=NodeType.QUOTE,
                        children=self.parse_children(node, image_map)
                    )
                ]

            # --------------------
            # Lists
            # --------------------

            case "ul":
                print("match ul")
                return [
                    Node(
                        type=NodeType.LIST,
                        metadata={"ordered": False},
                        children=self.parse_children(node, image_map)
                    )
                ]

            case "ol":

                return [
                    Node(
                        type=NodeType.LIST,
                        metadata={"ordered": True},
                        children=self.parse_children(node, image_map)
                    )
                ]

            case "li":
                print("match li")
                return [
                    Node(
                        type=NodeType.LIST_ITEM,
                        children=self.parse_children(node, image_map)
                    )
                ]

            # --------------------
            # Image
            # --------------------

            case "img":

                filename = Path(node.get("src", "")).name

                return [
                    Node(
                        type=NodeType.IMAGE,
                        metadata={
                            "src": image_map.get(filename)
                        }
                    )
                ]

            # --------------------
            # Table
            # --------------------

            case "table":

                return [
                    Node(
                        type=NodeType.TABLE,
                        children=self.parse_children(node, image_map)
                    )
                ]

            case "tr":

                return [
                    Node(
                        type=NodeType.ROW,
                        children=self.parse_children(node, image_map)
                    )
                ]

            case "td" | "th":

                return [
                    Node(
                        type=NodeType.CELL,
                        children=self.parse_children(node, image_map)
                    )
                ]

            # --------------------
            # Code
            # --------------------

            case "pre":

                return [
                    Node(
                        type=NodeType.CODE,
                        text=node.get_text("\n")
                    )
                ]

            case "code":

                return [
                    Node(
                        type=NodeType.CODE,
                        text=node.get_text()
                    )
                ]

            # --------------------
            # MathML
            # --------------------

            case "math":
                return [
                    Node(
                        type=NodeType.FORMULA,
                        metadata={
                            "raw": str(MathMLToLaTeX().convert(str(node)))
                        }
                    )
                ]

            # --------------------
            # Containers transparentes
            # --------------------

            case _:

                return self.parse_children(node, image_map)

    # -------------------------
    # Documento
    # -------------------------

    def extract_text(self, file_path):
        self.__check_file_existence(file_path)

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

            document.children.extend(
                self.parse_children(body, image_map)
            )

        return document

    # -------------------------
    # Imagens
    # -------------------------

    def extract_images(self, file_path):

        book = epub.read_epub(file_path)

        image_map = {}

        for img in book.get_items_of_type(ITEM_IMAGE):

            local_path = output_dir / Path(img.file_name).name

            with open(local_path, "wb") as f:
                f.write(img.get_content())

            image_map[Path(img.file_name).name] = str(local_path)

        return image_map

    def __check_file_existence(self, file_path: str) -> None:
        file_path = Path(file_path)

        if not file_path.is_file():
            raise ValueError("The file does not exists")
 