from pathlib import Path
from exceptions.PipelineException import BookProcessingError
from export.bookExporter import DEFAULT_OUTPUT_DIR
from export.pageTree import write_page_jsons
from file_inspection.provider.fileTypeDetectionProvider import FileTypeDetection
from log.loggerService import LoggerService
from models.Book import Book
from models.PipelineResult import PipelineResult
from models.enum.BookStatus import BookStatus
from parsers.factory import parserFactory
from processing.chunker import Chunker
from processing.paginator import Paginator
from processing.sentence_splitter import Splitter
from queues.audioProducer import publish_book_chunks
from queues.redisQueue import AudioQueue
from queues.resultMerger import merge_results
import logging

from storage.book.bookRepositoryProvider import BookRepositoryProvider
from storage.bucket.bucketProvider import BucketProvider

logger = logging.getLogger(__name__)

class BookPipeline():

    def __init__(self, db2: BookRepositoryProvider,splitter: Splitter, chunker: Chunker, parser_factory: parserFactory.ParserFactory,filetypeDetection: FileTypeDetection, paginator: Paginator, audio_queue: AudioQueue,storageService:BucketProvider,output_dir: Path = DEFAULT_OUTPUT_DIR):
        self.splitter = splitter
        self.chunker = chunker
        self.parser_factory = parser_factory
        self.filetypeDetection = filetypeDetection
        self.paginator = paginator
        self.audio_queue = audio_queue
        self.output_dir = output_dir
        self.db = db2
        self.storageService = storageService

    async def pipeline(self, file_path: Path) -> PipelineResult:
        LoggerService.log_info(f"BookPipeline - received file_path {file_path} to create audio")

        try:
            extension = self.filetypeDetection.detect_extension(file_path)
            parser = self.parser_factory.create(extension)
            content = parser.extract_text(file_path)
            paginated = self.paginator.paginate(content, file_path.stem)
            total_sentences = sum(len(page_data.sentences) for page_data in paginated.pages)
            LoggerService.log_info(
                "BookPipeline - generated book '%s' with %d pages and %d sentences",
                paginated.book.title, len(paginated.pages), total_sentences
            )
        except Exception as e:
            LoggerService.log_exception(
                "Error extracting text from %s",
                file_path
            )
            raise e

        try:
            await self.storageService.upload("test.txt", "helo, world!")
            chunk_datas = self.chunker.chunk_book(paginated)
            await self.db.create(Book(book_url="test", author="test", completed_pages=0))
            messages = publish_book_chunks(self.audio_queue, paginated.book, chunk_datas)
#
            #expected_chunk_ids = {m["chunk_id"] for m in messages}
            #responses = self.audio_queue.wait_for_results(expected_chunk_ids) if #expected_chunk_ids else {}
#
            #merge_results(paginated, responses, chunk_datas)
            #write_page_jsons(paginated, self.output_dir)
            #paginated.book.status = BookStatus.COMPLETED
            #paginated.book.completed_pages = paginated.book.total_pages
        except Exception as e:
            LoggerService.log_exception(
                "Error generating audio for %s",
                file_path
            )
            raise BookProcessingError("An error occurred when trying to generate audio")

        #return PipelineResult(
        #    file_path=file_path,
        #    chunks=len(chunk_datas),
        #    audio_generated=len(responses) == len(chunk_datas) if chunk_datas else False,
        #    json_path=str("")
        #)
        return ""
