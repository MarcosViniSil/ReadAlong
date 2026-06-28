from typing import Callable
from exceptions.PipelineException import UnsupportedFileFormat
from log.loggerService import LoggerService
from parsers.bookParserProvider import BookParser

class ParserFactory:
    def __init__(self,parsers: dict[str, Callable[[], BookParser]]):
        self.parsers = parsers

    def create(self,extension: str) -> BookParser:
        factory = self.parsers.get(extension)

        if not factory:
            LoggerService.log_error(
                "Unsupported file extension requested: '%s'. No matching parser factory registered.",
                extension
            )
            raise UnsupportedFileFormat(
                f"The extension '{extension}' is not supported"
            )

        parser = factory()
        LoggerService.log_info(
            "Parser instance created for extension '%s': %s",
            extension,
            type(parser).__name__
        )
        return parser