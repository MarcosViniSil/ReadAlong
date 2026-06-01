from fastapi import Request
from fastapi.responses import JSONResponse

from exceptions.PipelineException import (
    UnsupportedFileFormat,
    BookProcessingError,
    TextExtractionError
)

async def unsupported_file_handler(
    request: Request,
    exc: UnsupportedFileFormat
):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

async def text_extraction_error(
    request: Request,
    exc: TextExtractionError
):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

async def book_processing_handler(
    request: Request,
    exc: BookProcessingError
):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )