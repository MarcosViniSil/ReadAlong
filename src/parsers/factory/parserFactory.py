from typing import Callable
from exceptions.PipelineException import UnsupportedFileFormat
from parsers.bookParserProvider import BookParser

class ParserFactory:
    def __init__(self,parsers: dict[str, Callable[[], BookParser]]):
        self.parsers = parsers

    def create(self,extension: str) -> BookParser:        
        factory = self.parsers.get(extension)

        if not factory:
            raise UnsupportedFileFormat(
                f"The extension '{extension}' is not supported"
            )

        return factory()