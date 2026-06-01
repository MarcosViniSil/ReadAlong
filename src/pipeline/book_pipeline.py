from fastapi import File, UploadFile
from exceptions.PipelineException import BookProcessingError, TextExtractionError
from log.loggerService import LoggerService
from models.PipelineResult import PipelineResult
from parsers import parserFactory
from processing.sentence_splitter import Splitter
from tts.TTSProvider import TTSProvider
import logging

logger = logging.getLogger(__name__)

class BookPipeline():
    
    def __init__(self,splitter:Splitter,ttsService:TTSProvider,parser_factory: parserFactory.ParserFactory):
        self.splitter = splitter
        self.ttsService = ttsService
        self.parser_factory = parser_factory
        
    def pipeline(self,file_path: str) -> None:
        LoggerService.log_info(f"BookPipeline - received file_path {file_path} to create audio")
        
        try:
            parser = self.parser_factory.create(file_path)
            content = parser.extract_text(file_path)

        except Exception as e:
            LoggerService.log_exception(
                "Error extracting text from %s",
                file_path
            )
            raise e
        
        LoggerService.log_info(f"BookPipeline - content from file path {file_path} received and with length of {len(content)}")
        
        try:
            phrases = self.splitter.split_into_chunks(content)
            self.ttsService.generate("test",phrases)
        except Exception as e:
            LoggerService.log_exception(
                "Error splitting content into chunks and generating audio %s",
                file_path
            )
            raise BookProcessingError("An error occurred when trying to generate audio")
        
        LoggerService.log_info(f"BookPipeline - audio generated successfully with {len(phrases)} phrases")
  
        return PipelineResult(
            file_path=file_path,
            chunks=len(phrases),
            audio_generated=True
        )