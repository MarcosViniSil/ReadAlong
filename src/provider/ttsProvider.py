from fastapi import Depends, Request

from parsers.factory.parserFactory import ParserFactory
from pipeline.book_pipeline import BookPipeline
from processing.chunker import Chunker
from processing.paginator import Paginator
from processing.sentence_splitter import Splitter
from provider.fileInspectionProvider import getfileTypeDetection
from provider.parseFactoryProvider import getParseFactory
from queues.redisQueue import AudioQueue
from storage.pageRepository.impl.pageRepositoryImpl import PageRepositoryImpl
from storage.pageRepository.pageRepositoryProvider import PageRepositoryProvider
from storage.processingRun.impl.ProcessingRunRepositoryImpl import ProcessingRunRepositoryImpl
from storage.processingRun.processingRunRepositoryProvider  import ProcessingRunRepositoryProvider
from storage.book.bookRepositoryProvider import BookRepositoryProvider
from storage.book.impl.bookRepositoryImpl import BookRepositoryImpl
from storage.connection.database import Database
from storage.connection.factory import create_pool

def getSplitter() -> Splitter:
    return Splitter()

def getChunker() -> Chunker:
    return Chunker()

def getPaginator() -> Paginator:
    return Paginator()

def get_parser_factory() -> ParserFactory:
    return ParserFactory()

def get_audio_queue() -> AudioQueue:
    return AudioQueue()

def get_database(request: Request) -> Database:
    return request.app.state.db

def get_storage(request: Request):
    return request.app.state.storage

def get_book_repository(
    db: Database = Depends(get_database),
) -> BookRepositoryProvider:

    return BookRepositoryImpl(db)

def get_processing_run_repository(
    db: Database = Depends(get_database),
) -> ProcessingRunRepositoryProvider:

    return ProcessingRunRepositoryImpl(db)

def get_page_repository(
    db: Database = Depends(get_database),
) -> PageRepositoryProvider:

    return PageRepositoryImpl(db)

def getBookPipelineService(
    repository: BookRepositoryProvider = Depends(get_book_repository),
    processing_run_repository: ProcessingRunRepositoryProvider = Depends(get_processing_run_repository),
    page_repository:PageRepositoryProvider = Depends(get_page_repository),
    client: BookRepositoryImpl = Depends(get_storage)
) -> BookPipeline:

    return BookPipeline(
        repository,
        getSplitter(),
        getChunker(),
        getParseFactory(),
        getfileTypeDetection(),
        getPaginator(),
        get_audio_queue(),
        client,
        processing_run_repository,
        page_repository,
    )

