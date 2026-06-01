from fastapi import FastAPI

from exceptions.handlers import (
    unsupported_file_handler,
    book_processing_handler,
    text_extraction_error
)

from exceptions.PipelineException import (
    UnsupportedFileFormat,
    BookProcessingError,
    TextExtractionError
)

def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(
        UnsupportedFileFormat,
        unsupported_file_handler
    )

    app.add_exception_handler(
        BookProcessingError,
        book_processing_handler
    )
    
    app.add_exception_handler(
        TextExtractionError,
        text_extraction_error
    )