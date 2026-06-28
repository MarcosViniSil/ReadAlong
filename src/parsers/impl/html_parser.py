from pathlib import Path
from log.loggerService import LoggerService
from models.Node import Node
from models.enum.HtmlTag import HtmlTag
from mathml_to_latex.converter import MathMLToLaTeX
from bs4 import NavigableString, Tag
from models.enum.NodeType import NodeType

class HTMLParser:
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
        LoggerService.log_info("HTMLParser initialized with %d tag handlers", len(self.handlers))

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