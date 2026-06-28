from enum import Enum


class HtmlTag(Enum):
    PARAGRAPH = "p"
    LIST = "ul"
    UNORDERED_LIST = "ul"
    ORDERED_LIST = "ol"
    LIST_ITEM = "li"
    IMAGE = "img"
    MATH = "math"
    TABLE = "table"
    HEADER_1 = "h1"
    HEADER_2 = "h2"
    HEADER_3 = "h3"
    HEADER_4 = "h4"
    HEADER_5 = "h5"
    HEADER_6 = "h6"
    BLOCKQUOTE = "blockquote"
    TABLE_ROW = "tr"
    TABLE_DATA = "td"
    TABLE_HEADER = "th"
    PRE = "pre"
    CODE = "code"
    