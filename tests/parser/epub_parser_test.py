"""Test suite for EpubParser covering all node types and edge cases."""

import pytest

from models.Node import Node
from models.NodeType import NodeType
from parsers.impl.epub_parser import EpubParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser():
    return EpubParser()


# ---------------------------------------------------------------------------
# Helper assertions
# ---------------------------------------------------------------------------

def assert_heading(node, expected_level, expected_text=None):
    assert node.type == NodeType.HEADING
    assert node.metadata.get("level") == expected_level
    if expected_text is not None:
        assert len(node.children) == 1
        assert node.children[0].type == NodeType.TEXT
        assert expected_text in node.children[0].text


def assert_paragraph_with_text(node, expected_text=None):
    assert node.type == NodeType.PARAGRAPH
    if expected_text is not None:
        texts = [c.text for c in node.children if c.type == NodeType.TEXT]
        combined = " ".join(texts)
        assert expected_text in combined


def assert_image(node, expected_path=None):
    assert node.type == NodeType.IMAGE
    if expected_path:
        assert node.metadata.get("src") and expected_path in node.metadata["src"]


def assert_list(node, ordered):
    assert node.type == NodeType.LIST
    assert node.metadata.get("ordered") == ordered


def assert_list_item(node):
    assert node.type == NodeType.LIST_ITEM


def assert_table(node):
    assert node.type == NodeType.TABLE


def assert_row(node):
    assert node.type == NodeType.ROW


def assert_cell(node):
    assert node.type == NodeType.CELL


def assert_code(node, expected_text=None):
    assert node.type == NodeType.CODE
    if expected_text is not None:
        assert expected_text in node.text
    
def assert_not_none_and_node_instance(doc):
    assert doc is not None
    assert isinstance(doc, Node)


def assert_formula(node):
    assert node.type == NodeType.FORMULA
    assert "raw" in node.metadata
    assert node.metadata["raw"]


# ===================================================================
# Headings (h1 to h6)
# ===================================================================

class TestHeadings:
    """Each heading fixture has 3 headings of the same level."""

    @pytest.mark.parametrize("fixture,level,texts", [
        ("title-h1", 1, ["Título de Nível 1"]),
        ("title-h2", 2, ["Título de Nível 2"]),
        ("title-h3", 3, ["Título de Nível 3"]),
        ("title-h4", 4, ["Título de Nível 4"]),
        ("title-h5", 5, ["Título de Nível 5"]),
        ("title-h6", 6, ["Título de Nível 6"]),
    ])
    def test_heading_level(self, parser, fixture, level, texts):
        doc = parser.extract_text(f"tests/fixtures/epub/{fixture}.epub")
        assert_not_none_and_node_instance(doc)
        assert doc.type == NodeType.DOCUMENT
        assert len(doc.children) == 3
        for child in doc.children:
            assert_heading(child, level)
            text = child.children[0].text
            assert any(t in text for t in texts)

    def test_heading_h1_content(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/title-h1.epub")
        assert_not_none_and_node_instance(doc)
        titles = ["Este é um Título de Nível 1", "Outro Título de Nível 1", "Outro outro Título de Nível 1"]
        for i, child in enumerate(doc.children):
            assert_heading(child, 1, titles[i])

    def test_heading_h4_content(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/title-h4.epub")
        assert_not_none_and_node_instance(doc)
        titles = ["Este é um Título de Nível 4", "Outro Título de Nível 4", "Outro outro Título de Nível 4"]
        for i, child in enumerate(doc.children):
            assert_heading(child, 4, titles[i])


# ===================================================================
# Paragraphs and Text
# ===================================================================

class TestParagraphs:
    def test_multiple_short_texts(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/multiple-short-texts.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 8
        for child in doc.children:
            assert_paragraph_with_text(child)

    def test_multiple_long_texts(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/multiple-long-texts.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 3
        assert_paragraph_with_text(doc.children[0], "Lorem 1")
        assert_paragraph_with_text(doc.children[1], "Lorem 2")
        assert_paragraph_with_text(doc.children[2], "Lorem 3")

    def test_text_inside_div(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/text-inside-div.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 4
        for child in doc.children:
            assert_paragraph_with_text(child)

    def test_section_text(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/section-text.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 8
        for child in doc.children:
            assert child.type == NodeType.PARAGRAPH


class TestTextFormatting:
    def test_text_strong(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/text-strong.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 5
        assert_paragraph_with_text(doc.children[0], "Textos com Ênfase Forte")
        texts = [c.text for c in doc.children[1].children if c.type == NodeType.TEXT]
        assert any("negrito" in t or "strong" in t for t in texts)

    def test_text_em(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/text-em.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 4
        for child in doc.children:
            assert child.type == NodeType.PARAGRAPH
            texts = [c.text for c in child.children if c.type == NodeType.TEXT]
            assert texts

    def test_span_inside_div_and_p(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/span-inside-div-and-p.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 2
        for child in doc.children:
            assert child.type == NodeType.PARAGRAPH

    def test_span_p_and_em(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/span-p-and-em.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 3
        # Second paragraph has mixed span/em children
        p2 = doc.children[1]
        assert p2.type == NodeType.PARAGRAPH
        assert len(p2.children) >= 4


# ===================================================================
# Lists
# ===================================================================

class TestLists:
    def test_ordered_list(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/ordered-list.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 1
        assert_list(doc.children[0], ordered=True)
        assert len(doc.children[0].children) == 5
        for item in doc.children[0].children:
            assert_list_item(item)

    def test_unordered_list(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/unordered-list.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 1
        assert_list(doc.children[0], ordered=False)
        assert len(doc.children[0].children) == 5
        for item in doc.children[0].children:
            assert_list_item(item)


# ===================================================================
# Tables
# ===================================================================

class TestTables:
    def test_semantic_table(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/semantic-table.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 1
        assert_table(doc.children[0])
        # thead(1 row) + tbody(3 rows) + tfoot(1 row) = 5
        assert len(doc.children[0].children) == 5
        for row in doc.children[0].children:
            assert_row(row)

    def test_non_semantic_table(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/non-semantic-table.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 1
        assert_table(doc.children[0])
        assert len(doc.children[0].children) == 4  # 4 tr rows
        for row in doc.children[0].children:
            assert_row(row)

    def test_plain_table(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/table.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 1
        assert_table(doc.children[0])
        rows = doc.children[0].children
        assert len(rows) == 9
        for row in rows:
            assert_row(row)
            for cell in row.children:
                assert_cell(cell)


# ===================================================================
# Images
# ===================================================================

class TestImages:
    def test_only_images(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/only-images.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 2
        for child in doc.children:
            assert_image(child)

    def test_images_with_link(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/images-w-link.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 4


# ===================================================================
# Code
# ===================================================================

class TestCode:
    def test_only_pre_code(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/only-pre-code.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 2
        for child in doc.children:
            assert_code(child)

    def test_pre_and_code(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/pre-and-code.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 2
        assert_heading(doc.children[0], 1)
        assert_code(doc.children[1], "def fibonacci")

    def test_only_code(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/only-code.epub")
        assert_not_none_and_node_instance(doc)

        # Only-code epub mixes <code> inside <p> tags,
        # so they come out as Paragraph nodes
        assert len(doc.children) == 40
        for child in doc.children:
            assert child.type == NodeType.PARAGRAPH


# ===================================================================
# Math formulas
# ===================================================================

class TestMath:
    def test_only_math(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/only-math.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 5
        assert_heading(doc.children[0], 1, "Fórmulas Matemáticas")
        assert_formula(doc.children[1])
        assert_paragraph_with_text(doc.children[2], "Equação de Einstein")
        assert_formula(doc.children[3])
        assert_paragraph_with_text(doc.children[4], "Função quadrática")


# ===================================================================
# Links
# ===================================================================

class TestLinks:
    def test_only_links(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/only-links.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 3
        for child in doc.children:
            assert child.type == NodeType.TEXT

    def test_links_and_text(self, parser):
        doc = parser.extract_text("tests/fixtures/epub/links-and-text.epub")
        assert_not_none_and_node_instance(doc)
        assert len(doc.children) == 3
        for child in doc.children:
            assert child.type == NodeType.PARAGRAPH


# ===================================================================
# Error handling
# ===================================================================

class TestErrorHandling:
    def test_file_not_found(self, parser):
        with pytest.raises(ValueError, match="file does not exists"):
            parser.extract_text("tests/fixtures/epub/non-existent-file.epub")
