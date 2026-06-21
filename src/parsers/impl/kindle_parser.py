from parsers.bookParserProvider import BookParser
from pathlib import Path
import subprocess

output_dir = Path("kindle_converted")
output_dir.mkdir(exist_ok=True)

class KindleParser(BookParser):

    def __init__(self,parser:BookParser):
        self.parser = parser

    def extract_text(self, file_path: Path) -> str:
        epub_path = self.__convert_kindle_to_epub(file_path)

        self.parser.extract_text(epub_path)

        return ""

    def __convert_kindle_to_epub(self,kindle_path:Path) -> str:
        
        file_name = kindle_path.stem        
        converted_kindle_path = f"{output_dir}/{file_name}.epub"

        subprocess.run(
            ["ebook-convert", kindle_path, converted_kindle_path],
            check=True
        )

        return converted_kindle_path