from datetime import datetime
from pathlib import Path
import uuid
from exceptions.PipelineException import BookProcessingError
from export.bookExporter import DEFAULT_OUTPUT_DIR
from export.pageTree import write_page_jsons
from file_inspection.provider.fileTypeDetectionProvider import FileTypeDetection
from log.loggerService import LoggerService
from models.Page import Page
from models.ProcessingRun import ProcessingRun
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
from storage.pageRepository.pageRepositoryProvider import PageRepositoryProvider
from storage.processingRun.processingRunRepositoryProvider import ProcessingRunRepositoryProvider
from storage.book.bookRepositoryProvider import BookRepositoryProvider
from storage.bucket.bucketProvider import BucketProvider

logger = logging.getLogger(__name__)

class BookPipeline():

    def __init__(self, db2: BookRepositoryProvider,splitter: Splitter, chunker: Chunker, parser_factory: parserFactory.ParserFactory,filetypeDetection: FileTypeDetection, paginator: Paginator, audio_queue: AudioQueue,storageService:BucketProvider,processing_run_repository:ProcessingRunRepositoryProvider,pageRepository: PageRepositoryProvider,output_dir: Path = DEFAULT_OUTPUT_DIR):
        self.splitter = splitter
        self.chunker = chunker
        self.parser_factory = parser_factory
        self.filetypeDetection = filetypeDetection
        self.paginator = paginator
        self.audio_queue = audio_queue
        self.output_dir = output_dir
        self.db = db2
        self.storageService = storageService
        self.processing_run_repository = processing_run_repository
        self.pageRepository = pageRepository

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
            processing_run:ProcessingRun = await self.processing_run_repository.create("36d657b2-db02-46a2-8b63-1f8c4ea00a38")

            chunk_datas = self.chunker.chunk_book(paginated)
            await self.db.create(Book(book_url="test", author="test", completed_pages=0, total_pages=paginated.book.total_pages))
            #messages = publish_book_chunks(self.audio_queue, paginated.book, chunk_datas)
#
            #expected_chunk_ids = {m["chunk_id"] for m in messages}
            #responses = self.audio_queue.wait_for_results(expected_chunk_ids) if #expected_chunk_ids else {}
#
            #merge_results(paginated, responses, chunk_datas)
            
            pages_path = write_page_jsons(paginated, self.output_dir)
            pages_saved_on_database : list[str] = []
            for path in pages_path:
                path_bucket = f"{str(uuid.uuid4())}.json"
                await self.storageService.upload(path_bucket, str(path),content_type="application/json")

                pages_saved_on_database.append(path_bucket)

            for i,page_saved in enumerate(pages_saved_on_database):
                await self.pageRepository.create(Page(processing_run_id=processing_run.id,sequence= i + 1, page_url=page_saved, sentence_count=len(chunk_datas), status=BookStatus.PENDING,created_at=datetime.now(),updated_at= None))
            
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
