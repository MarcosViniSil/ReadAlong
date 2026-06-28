from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from ebooklib import ITEM_IMAGE, epub
from mathml_to_latex.converter import MathMLToLaTeX
from models.Node import Node
from models.enum.HtmlTag import HtmlTag
from models.enum.NodeType import NodeType
from parsers.bookParserProvider import BookParser


output_dir = Path("imgs")
output_dir.mkdir(exist_ok=True)


class EpubParser(BookParser):

    def __init__(self):
        self.handlers = {
            HtmlTag.PARAGRAPH: self.parse_paragraph,
            HtmlTag.UNORDERED_LIST: self.parse_unordered_list,
            HtmlTag.ORDERED_LIST: self.parse_ordered_list,
            HtmlTag.LIST_ITEM: self.parse_list_item,
            HtmlTag.IMAGE: self.parse_image,
            HtmlTag.MATH: self.parse_math_tag,
            HtmlTag.TABLE: self.parse_table,
            HtmlTag.HEADER_1: self.parse_heading,
            HtmlTag.HEADER_2: self.parse_heading,
            HtmlTag.HEADER_3: self.parse_heading,
            HtmlTag.HEADER_4: self.parse_heading,
            HtmlTag.HEADER_5: self.parse_heading,
            HtmlTag.HEADER_6: self.parse_heading,
            HtmlTag.BLOCKQUOTE: self.parse_blockquote,
            HtmlTag.TABLE_ROW: self.parse_table_row,
            HtmlTag.TABLE_DATA: self.parse_table_data,
            HtmlTag.TABLE_HEADER: self.parse_table_data,
            HtmlTag.PRE: self.parse_pre_tag,
            HtmlTag.CODE: self.parse_code_tag,
        }
        self.math_converter = MathMLToLaTeX()

    def parse_children(self, parent, image_map):
        for child in parent.children:
            yield from self.parse_node(child, image_map)

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

        if isinstance(node, NavigableString):
            return self.text_node(node)

        if not isinstance(node, Tag):
            return []

        try:
            handler = self.handlers.get(HtmlTag(node.name))
        except ValueError:
            handler = None

        if handler:
            return handler(node, image_map)

        return self.parse_children(node, image_map)
    
    def parse_tag(self, node, image_map:dict, tag:NodeType, metadata:dict):
        return [
            Node(
            type=tag,
            metadata= metadata or {},
            children=list(self.parse_children(node, image_map))
            )
        ]

    def parse_paragraph(self, node, image_map):
        return self.parse_tag(node,image_map,NodeType.PARAGRAPH,None)

    def parse_heading(self, node, image_map):
        metadata = {"level": int(node.name[1])}
        return self.parse_tag(node,image_map,NodeType.HEADING,metadata)
    
    def parse_blockquote(self, node, image_map):
        return self.parse_tag(node,image_map,NodeType.QUOTE,None)  

    def parse_unordered_list(self, node, image_map):
        metadata={"ordered": False}
        return self.parse_tag(node,image_map,NodeType.LIST,metadata)       

    def parse_ordered_list(self, node, image_map):
        metadata={"ordered": True}
        return self.parse_tag(node,image_map,NodeType.LIST,metadata)

    def parse_list_item(self, node, image_map):
        return self.parse_tag(node,image_map,NodeType.LIST_ITEM,None)  

    
    def parse_image(self, node, image_map):
        filename = Path(node.get("src", "")).name
        metadata={"src": image_map.get(filename)}
        return self.parse_tag(node,image_map,NodeType.IMAGE,metadata)  
     

    def parse_table(self, node, image_map):
        return self.parse_tag(node,image_map,NodeType.TABLE,None)  


    def parse_table_row(self, node, image_map):
        return self.parse_tag(node,image_map,NodeType.ROW,None)  

    def parse_table_data(self, node, image_map):
        return self.parse_tag(node,image_map,NodeType.CELL,None)  


    def parse_pre_tag(self, node, image_map):
        return [
            Node(
                type=NodeType.CODE,
                text=node.get_text()
            )
        ]

    def parse_code_tag(self, node, image_map):
        return [
            Node(
                type=NodeType.CODE,
                text=node.get_text()
            )
        ]
    

    def parse_math_tag(self, node, image_map):
        metadata={"raw": self.math_converter.convert(str(node))}
        return self.parse_tag(node,image_map,NodeType.FORMULA,metadata)  

    # -------------------------
    # Documento
    # -------------------------

    def extract_text(self, file_path):
        self.__check_file_existence(file_path)

        book = epub.read_epub(file_path)

        image_map = self.extract_images(book)

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

    def extract_images(self, book):
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
 