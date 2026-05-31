from pathlib import Path
import magic
import mimetypes
from parsers.base import BookParser
from parsers.txt_parser import TxtParser

class ParserFactory:

    @staticmethod
    def create(file_path: str) -> BookParser:
        mime_type = magic.from_file(file_path, mime=True)
        extension = mimetypes.guess_extension(mime_type)
        
        if extension == ".txt":
            return TxtParser()

        raise ValueError(
            f"Format don't supported: {extension}"
        )