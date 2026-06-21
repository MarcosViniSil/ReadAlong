from fastapi import Depends

from parsers.factory.parserFactory import ParserFactory
from pipeline.book_pipeline import BookPipeline
from processing.sentence_splitter import Splitter
from provider.fileInspectionProvider import getfileTypeDetection
from provider.parseFactoryProvider import getParseFactory
from tts import TTSProvider
from tts.imp.TTSProviderImpl import KokoroProviderImpl

def getSplitter() -> Splitter:
    return Splitter()

def getTTSProvider() -> TTSProvider:
    return KokoroProviderImpl()

def get_parser_factory() -> ParserFactory:
    return ParserFactory()

def getBookPipelineService() -> BookPipeline:
    return BookPipeline(
        getSplitter(),
        getTTSProvider(),
        getParseFactory(),
        getfileTypeDetection()
    )

