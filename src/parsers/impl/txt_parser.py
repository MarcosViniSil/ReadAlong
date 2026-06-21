from parsers.bookParserProvider import BookParser

class TxtParser(BookParser):

    def extract_text(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return str(f.read())