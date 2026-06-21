from pathlib import Path
import magic
import mimetypes
from exceptions.PipelineException import BookProcessingError
from file_inspection.provider.fileTypeDetectionProvider import FileTypeDetection
from log.loggerService import LoggerService

class ExtensionDetector(FileTypeDetection):
    
    MIME_TO_EXTENSION = {
        'application/epub+zip': '.epub',
        'application/x-mobipocket-ebook': '.mobi',
        'application/pdf': '.pdf',
        'text/plain': '.txt',
        'application/zip': '.epub',
    }

    def __get_extension_from_mime(self,mime_type: str) -> str:        
        if mime_type in self.MIME_TO_EXTENSION:
            return self.MIME_TO_EXTENSION[mime_type]
        
        ext = mimetypes.guess_extension(mime_type)
        return ext if ext else ''
    
    def detect_extension(self,file_path: Path) -> str:
        try:
            mime_type = magic.from_file(file_path, mime=True)
            extension = self.__get_extension_from_mime(mime_type)
            LoggerService.log_info(f"mime_type: {mime_type}, for file path {file_path}")
            LoggerService.log_info(f"File extension verified: {extension} for file path {file_path}")
            return extension
        except Exception as e:
            LoggerService.log_exception(
                "ParserFactory - Error when trying to verify file extension %s",
                e
            )
            raise BookProcessingError("An error occurred when trying to verify file extension")