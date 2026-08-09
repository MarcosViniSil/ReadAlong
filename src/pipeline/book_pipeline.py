from pathlib import Path
from exceptions.PipelineException import BookProcessingError
from export.bookExporter import DEFAULT_OUTPUT_DIR, write_book_json
from file_inspection.provider.fileTypeDetectionProvider import FileTypeDetection
from log.loggerService import LoggerService
from models.Book import Book
from models.PipelineResult import PipelineResult
from models.SentenceType import SentenceType
from parsers.factory import parserFactory
from processing.paginator import Paginator
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
            book = self.paginator.paginate(content, file_path.stem)
            print("book: ",book)
            total_sentences = sum(len(page.Sentence) for page in book.pages)
            LoggerService.log_info(
                "BookPipeline - generated book '%s' with %d pages and %d sentences",
                book.bookName, len(book.pages), total_sentences
            )
        except Exception as e:
            LoggerService.log_exception(
                "Error extracting text from %s",
                file_path
            )
            raise e
        
        try:
            self.__generate_audio(book)
            json_path = write_book_json(book, self.output_dir)
        except Exception as e:
            LoggerService.log_exception(
                "Error generating audio for %s",
                file_path
            )
            raise BookProcessingError("An error occurred when trying to generate audio")

        return PipelineResult(
            file_path=file_path,
            chunks=len(book.pages),
            audio_generated=bool(book.pages and book.pages[0].audioFile),
            json_path=str(json_path)
        )

    def __generate_audio(self, book: Book) -> None:
        spoken = [
            sentence
            for page in book.pages
            for sentence in page.Sentence
            if sentence.sentenceType == SentenceType.TEXT and sentence.text
        ]

        if not spoken:
            LoggerService.log_warning("BookPipeline - no spoken sentences to synthesize")
            return

        transcription = self.ttsService.generate(
            book.bookName,
            [sentence.text for sentence in spoken]
        )

        for sentence, duration in zip(spoken, transcription.durations):
            sentence.duration = duration

        cursor = 0.0
        for page in book.pages:
            for sentence in page.Sentence:
                sentence.start = cursor
                cursor += sentence.duration
                sentence.end = cursor
            page.audioFile = transcription.audio_path