from pathlib import Path

import pytest

from models.Node import Node
from models.NodeType import NodeType
from parsers.impl.epub_parser import EpubParser
from parsers.impl.kindle_parser import KindleParser
from parsers.impl.txt_parser import TxtParser

@pytest.fixture
def parser():
    return TxtParser()

def test_txt_parser_when_file_exists(parser) -> Node:
    file_path = Path("tests/fixtures/txt/example.txt")
    doc = parser.extract_text(file_path)
    assert doc is not None
    assert isinstance(doc, Node)
    assert len(doc.children) == 22
    for child in doc.children:
            assert child.type == NodeType.TEXT


def test_txt_parser_when_file_does_not_exists(parser) -> Node:
    file_path = Path("tests/fixtures/txt/file_does_not_exists.txt")
    with pytest.raises(ValueError, match="file does not exists"):
            parser.extract_text(file_path)
