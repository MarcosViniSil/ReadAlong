from models.enum.FileType import FileType
from parsers.impl.epub.epub_parser import EpubParser
from parsers.impl.html_parser import HTMLParser
from parsers.impl.kindle_parser import KindleParser
from parsers.factory.parserFactory import ParserFactory
from parsers.impl.txt_parser import TxtParser

def getParseFactory() -> ParserFactory:
    html_parser_factory = HTMLParser()
    epub_parser_factory = lambda: EpubParser(html_parser_factory)
    
    factory = ParserFactory({
        FileType.TXT.value: lambda: TxtParser(),
        FileType.EPUB.value: epub_parser_factory,
        FileType.MOBI.value: lambda: KindleParser(epub_parser_factory()),
        FileType.AMAZON.value: lambda: KindleParser(epub_parser_factory()),
    })

    return factory