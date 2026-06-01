from pathlib import Path
import magic
import mimetypes
from exceptions.PipelineException import BookProcessingError, UnsupportedFileFormat
from log.loggerService import LoggerService
from models.FileType import FileType
from parsers.base import BookParser
from parsers.txt_parser import TxtParser

class ParserFactory:

    @staticmethod
    def create(file_path: str) -> BookParser:
        try:
            mime_type = magic.from_file(file_path, mime=True)
            extension = mimetypes.guess_extension(mime_type)
        except Exception as e:
            LoggerService.log_exception(
                "ParserFactory - Error when trying to verify file extension %s",
                file_path
            )
            raise BookProcessingError("An error occurred when trying to verify file extension")
        
        if extension == FileType.TXT.value:
            return TxtParser()

        raise UnsupportedFileFormat(f"The {extension} extension is not allowed")