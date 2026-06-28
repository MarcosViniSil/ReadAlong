from pathlib import Path
import subprocess
from log.loggerService import LoggerService
from parsers.bookParserProvider import BookParser

output_dir = Path("kindle_converted")
output_dir.mkdir(exist_ok=True)

class KindleParser(BookParser):

    def __init__(self,parser:BookParser):
        self.parser = parser
        LoggerService.log_info("KindleParser initialized with underlying parser: %s", type(parser).__name__)

    def extract_text(self, file_path: Path) -> str:
        LoggerService.log_info("Starting Kindle text extraction for file: %s", file_path)
        self.__check_file_existence(file_path)
        epub_path = self.__convert_kindle_to_epub(file_path)

        LoggerService.log_info("Kindle file converted to EPUB; delegating text extraction to %s", type(self.parser).__name__)
        return self.parser.extract_text(epub_path)

    def __convert_kindle_to_epub(self,kindle_path:Path) -> str:

        file_name = kindle_path.stem
        converted_kindle_path = f"{output_dir}/{file_name}.epub"

        LoggerService.log_info("Converting Kindle file '%s' to EPUB at '%s'", kindle_path, converted_kindle_path)

        result = subprocess.run(
            ["ebook-convert", kindle_path, converted_kindle_path],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            LoggerService.log_error(
                "ebook-convert failed for '%s' (exit code %d): %s",
                kindle_path, result.returncode, result.stderr.strip()
            )
            result.check_returncode()

        LoggerService.log_info("Successfully converted Kindle file to EPUB: %s", converted_kindle_path)

        return converted_kindle_path

    def __check_file_existence(self, file_path: str) -> None:
        file_path = Path(file_path)

        if not file_path.is_file():
            LoggerService.log_error("File not found: %s", file_path)
            raise ValueError("The file does not exists")