
from pathlib import Path

import pytest

from models.Node import Node
from parsers.impl.epub.epub_parser import EpubParser
from parsers.impl.html_parser import HTMLParser
from parsers.impl.kindle_parser import KindleParser

@pytest.fixture
def parser():
    html_parser = HTMLParser()
    epub_parser = EpubParser(html_parser)
    return KindleParser(epub_parser)

def test_mobi_parser_when_file_exists(parser) -> Node:
    file_path = Path("tests/fixtures/mobi/sample.mobi")
    result = parser.extract_text(file_path)
    assert result is not None
    assert isinstance(result, Node)


def test_amazon_parser_when_file_exists(parser) -> Node:
    file_path = Path("tests/fixtures/azw3/famouspaintings.azw3")
    result = parser.extract_text(file_path)
    assert result is not None
    assert isinstance(result, Node)

def test_mobi_parser_when_file_does_not_exists(parser) -> Node:
    file_path = Path("tests/fixtures/mobi/file_does_not_exists.mobi")
    with pytest.raises(ValueError, match="file does not exists"):
            parser.extract_text(file_path)

def test_amazon_parser_when_file_does_not_exists(parser) -> Node:
    file_path = Path("tests/fixtures/azw3/file_does_not_exists.azw3")
    with pytest.raises(ValueError, match="file does not exists"):
            parser.extract_text(file_path)
