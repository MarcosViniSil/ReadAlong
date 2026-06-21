from models.Element import Element
from parsers.bookParserProvider import BookParser

class TxtParser(BookParser):

    def extract_text(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            content_splitted = content.split("\n")
            elements:list[Element] = []
            for row in content_splitted:
                elements.append(Element("p",row,None,None))

            return elements