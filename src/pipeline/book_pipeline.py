from datetime import datetime
from pathlib import Path
from exceptions.PipelineException import BookProcessingError
from export.bookExporter import DEFAULT_OUTPUT_DIR, book_code, page_code
from export.pageTree import write_page_jsons
from file_inspection.provider.fileTypeDetectionProvider import FileTypeDetection
from log.loggerService import LoggerService
from models.Job import Job
from models.AudioAsset import AudioAsset
from models.Page import Page
from models.ProcessingRun import ProcessingRun
from models.Book import Book
from models.PipelineResult import PipelineResult
from models.chunk import Chunk
from models.enum.BookStatus import BookStatus
from parsers.factory import parserFactory
from processing.chunker import ChunkData, Chunker
from processing.paginator import PaginatedBook, Paginator
from processing.sentence_splitter import Splitter
from queues.audioProducer import publish_messages
from queues.redisQueue import AudioQueue
from queues.resultMerger import merge_results
import logging
from storage.audioAssetRepository.audioAssetRepositoryProvider import AudioAssetRepositoryProvider
from storage.chunkRepository.chunkRepositoryProvider import ChunkRepositoryProvider
from storage.jobRepository.jobRepositoryProvider import JobRepositoryProvider
from storage.pageRepository.pageRepositoryProvider import PageRepositoryProvider
from storage.processingRun.processingRunRepositoryProvider import ProcessingRunRepositoryProvider
from storage.book.bookRepositoryProvider import BookRepositoryProvider
from storage.bucket.bucketProvider import BucketProvider

logger = logging.getLogger(__name__)

class BookPipeline():

    def __init__(self, db2: BookRepositoryProvider,splitter: Splitter, chunker: Chunker, parser_factory: parserFactory.ParserFactory,filetypeDetection: FileTypeDetection, paginator: Paginator, audio_queue: AudioQueue,storageService:BucketProvider,processing_run_repository:ProcessingRunRepositoryProvider,pageRepository: PageRepositoryProvider,chunk_repository: ChunkRepositoryProvider,audio_asset_repository: AudioAssetRepositoryProvider,jobRepository:JobRepositoryProvider,output_dir: Path = DEFAULT_OUTPUT_DIR):
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
        self.chunk_repository = chunk_repository
        self.audio_asset_repository = audio_asset_repository
        self.jobRepository = jobRepository

    async def pipeline(self, file_path: Path) -> PipelineResult:
        LoggerService.log_info(f"BookPipeline - received file_path {file_path} to create audio")

        try:
            extension = self.filetypeDetection.detect_extension(file_path)
            parser = self.parser_factory.create(extension)
            content = parser.extract_text(file_path)
            paginated:PaginatedBook = self.paginator.paginate(content, file_path.stem)
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
            # Book first: processing_run and pages reference it by FK.
            book: Book = await self.db.create(Book(
                title=paginated.book.title,
                book_url="test",
                author="test",
                completed_pages=0,
                total_pages=paginated.book.total_pages,
            ))
            processing_run: ProcessingRun = await self.processing_run_repository.create(book.id, len(paginated.pages))

            chunk_data:list[ChunkData] = self.chunker.chunk_book(paginated)

            # 1) Persist pages first, with deterministic S3 keys, so chunks
            #    can reference the real page ids returned by the DB.
            book_key = book_code(paginated.book.title)
            pages_stored: list[Page] = []
            for page_data in paginated.pages:
                page_key = f"books/{book_key}/pages/{page_code(page_data.page.sequence)}.json"
                pages_stored.append(await self.pageRepository.create(Page(
                    processing_run_id=processing_run.id,
                    sequence=page_data.page.sequence,
                    page_url=page_key,
                    sentence_count=len(page_data.sentences),
                    status=BookStatus.PENDING,
                    created_at=datetime.now(),
                    updated_at=None,
                )))
            pages_by_sequence = {page.sequence: page for page in pages_stored}

            # 2) Propagate the DB page ids into the chunks and persist them.
            #    Chunk ids are preserved so queue responses correlate by id.
            for chunk in chunk_data:
                db_page = pages_by_sequence[chunk.page.sequence]
                chunk.chunk.page_id = db_page.id
                chunk.page = db_page
            chunks_created:list[Chunk] = await self.chunk_repository.create_many([cd.chunk for cd in chunk_data])

            # 3) Queue round-trip: one job per chunk, wait for all results,
            #    merge word timings into each sentence's audio block.
            #messages = publish_book_chunks(self.audio_queue, book, chunk_data)
            #expected_chunk_ids = {m["chunk_id"] for m in messages}
            #responses = self.audio_queue.wait_for_results(expected_chunk_ids) if #expected_chunk_ids else {}
            #merge_results(paginated, responses, chunk_datas)

            jobs_created: list[Job] = await self.jobRepository.create_many(
                    [chunk.id for chunk in chunks_created])

            jobs_id = [{"job_id":job.id} for job in jobs_created]
            
            publish_messages(self.audio_queue,jobs_id)

            ## 4) Record each generated audio asset and mark its chunk done.
            #for chunk_data in chunk_datas:
            #    response = responses.get(chunk_data.chunk.id)
            #    if response is None:
            #        continue
            #    audio_url = response.get("audio_url", "")
            #    duration = max((s["end"] for s in response.get("sentences", [])), default=0#.0)
            #    await self.audio_asset_repository.create(AudioAsset(
            #        id="",
            #        chunk_id=chunk_data.chunk.id,
            #        storage_key=audio_url,
            #        format=audio_url.rsplit(".", 1)[-1] if "." in audio_url else "wav",
            #        duration=duration,
            #        size=0.0,
            #        status=BookStatus.COMPLETED,
            #        created_at=datetime.now(),
            #    ))
            #    await self.chunk_repository.update_status(chunk_data.chunk.id, BookStatus#.COMPLETED)

            # 5) Serialize AFTER the audio round-trip, so the page JSON carries
            #    each sentence's chunk_id plus the word timings from the worker.
            pages_path = write_page_jsons(paginated, self.output_dir)
            for path in pages_path:
                page_key = f"books/{book_key}/pages/{path.name}"
                await self.storageService.upload(page_key, str(path), content_type="application/json")

            #paginated.book.status = BookStatus.COMPLETED
            #paginated.book.completed_pages = paginated.book.total_pages
        except Exception as e:
            LoggerService.log_exception(
                "Error generating audio for %s",
                file_path
            )
            raise BookProcessingError("An error occurred when trying to generate audio")

        return PipelineResult(
            file_path=str(file_path),
            chunks=10,
            audio_generated="",
            json_path=str("")
        )
