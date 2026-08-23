from pathlib import Path
from exceptions.PipelineException import BookProcessingError
from export.bookExporter import DEFAULT_OUTPUT_DIR, write_book_json
from export.pageTree import write_page_jsons
from file_inspection.provider.fileTypeDetectionProvider import FileTypeDetection
from log.loggerService import LoggerService
from models.PipelineResult import PipelineResult
from models.SentenceType import SentenceType
from models.enum.BookStatus import BookStatus
from parsers.factory import parserFactory
from processing.paginator import PaginatedBook, Paginator
from processing.sentence_splitter import Splitter
from tts.TTSProvider import TTSProvider
import logging

logger = logging.getLogger(__name__)

class BookPipeline():

    def __init__(self,splitter:Splitter,ttsService:TTSProvider,parser_factory: parserFactory.ParserFactory, filetypeDetection: FileTypeDetection, paginator: Paginator, output_dir: Path = DEFAULT_OUTPUT_DIR):
        self.splitter = splitter
        self.ttsService = ttsService
        self.parser_factory = parser_factory
        self.filetypeDetection = filetypeDetection
        self.paginator = paginator
        self.output_dir = output_dir

    def pipeline(self,file_path: Path) -> None:
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
            #self.__generate_audio(paginated)
            #json_path = write_book_json(paginated, self.output_dir)
            write_page_jsons(paginated, self.output_dir)
            paginated.book.status = BookStatus.COMPLETED
            paginated.book.completed_pages = paginated.book.total_pages
        except Exception as e:
            LoggerService.log_exception(
                "Error generating audio for %s",
                file_path
            )
            raise BookProcessingError("An error occurred when trying to generate audio")

        return PipelineResult(
            file_path=file_path,
            chunks=len(paginated.pages),
            audio_generated=bool(paginated.pages and paginated.audio_file),
            json_path=str("")
        )

    def __generate_audio(self, paginated: PaginatedBook) -> None:
        spoken = [
            sentence
            for page_data in paginated.pages
            for sentence in page_data.sentences
            if sentence.sentenceType == SentenceType.TEXT and sentence.text
        ]

        if not spoken:
            LoggerService.log_warning("BookPipeline - no spoken sentences to synthesize")
            return

        transcription = self.ttsService.generate(
            paginated.book.title,
            [sentence.text for sentence in spoken]
        )

        for sentence, duration in zip(spoken, transcription.durations):
            sentence.duration = duration

        cursor = 0.0
        for page_data in paginated.pages:
            for sentence in page_data.sentences:
                sentence.start = cursor
                cursor += sentence.duration
                sentence.end = cursor

        paginated.audio_file = transcription.audio_path
