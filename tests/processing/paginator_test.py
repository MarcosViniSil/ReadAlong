from models.Node import Node
from models.SentenceType import SentenceType
from models.enum.NodeType import NodeType
from processing.paginator import Paginator

paginator = Paginator()


def build_document(*children) -> Node:
    return Node(type=NodeType.DOCUMENT, children=list(children))


def text_node(text: str) -> Node:
    return Node(type=NodeType.TEXT, text=text)


def paragraph(*sentences: str) -> Node:
    return Node(type=NodeType.PARAGRAPH, children=[text_node(s) for s in sentences])


def heading(level: int, text: str) -> Node:
    return Node(type=NodeType.HEADING, metadata={"level": level}, children=[text_node(text)])


def image(src: str) -> Node:
    return Node(type=NodeType.IMAGE, metadata={"src": src})


def formula(raw: str) -> Node:
    return Node(type=NodeType.FORMULA, metadata={"raw": raw})


def table(rows: list[list[str]]) -> Node:
    return Node(
        type=NodeType.TABLE,
        children=[
            Node(type=NodeType.ROW, children=[Node(type=NodeType.CELL, children=[text_node(c)]) for c in row])
            for row in rows
        ],
    )


def test_paginate_builds_book_with_single_page():
    doc = build_document(paragraph("Hello world."))
    book = paginator.paginate(doc, "My Book")

    assert book.bookName == "My Book"
    assert book.bookCode == "my-book"
    assert len(book.pages) == 1

    page = book.pages[0]
    assert page.pageCode == "P001"
    assert page.nextPageCode == ""
    assert len(page.Sentence) == 1
    assert page.Sentence[0].text == "Hello world."
    assert page.Sentence[0].sentenceType == SentenceType.TEXT


def test_paragraph_is_split_into_sentences():
    doc = build_document(paragraph("First sentence. Second sentence! Third?"))
    book = paginator.paginate(doc, "Book")

    texts = [s.text for s in book.pages[0].Sentence]
    assert texts == ["First sentence.", "Second sentence!", "Third?"]


def test_heading_becomes_spoken_sentence_with_level():
    doc = build_document(heading(1, "Introduction"))
    book = paginator.paginate(doc, "Book")

    sentence = book.pages[0].Sentence[0]
    assert sentence.text == "Introduction"
    assert sentence.sentenceType == SentenceType.TEXT


def test_heading_level_1_forces_page_break():
    doc = build_document(
        paragraph("Some intro text."),
        heading(1, "Chapter One"),
        paragraph("Chapter body."),
    )
    book = paginator.paginate(doc, "Book")

    assert len(book.pages) == 2
    assert book.pages[0].Sentence[0].text == "Some intro text."
    assert book.pages[1].Sentence[0].text == "Chapter One"
    assert book.pages[1].Sentence[1].text == "Chapter body."
    assert book.pages[0].nextPageCode == "P002"


def test_image_formula_table_become_non_spoken_markers():
    doc = build_document(
        paragraph("Before the figure."),
        image("cover.jpg"),
        formula(r"\frac{a}{b}"),
        table([["h1", "h2"], ["a", "b"]]),
        paragraph("After the figure."),
    )
    book = paginator.paginate(doc, "Book")

    types = [s.sentenceType for s in book.pages[0].Sentence]
    texts = [s.text for s in book.pages[0].Sentence]

    assert types == [
        SentenceType.TEXT,
        SentenceType.IMAGE,
        SentenceType.LATEX,
        SentenceType.TABLE,
        SentenceType.TEXT,
    ]
    assert texts[1] == ""
    assert texts[2] == ""
    assert texts[3] == "h1 | h2 ; a | b"


def test_pages_are_grouped_by_estimated_duration():
    # Each sentence has 7 words -> 7 / 2.5 = 2.8s.
    # 10 sentences = 28s <= 30s target; the 11th would push it to 30.8s.
    doc = build_document(*[paragraph(f"Words number {i} in this text block.") for i in range(11)])
    book = paginator.paginate(doc, "Book")

    assert len(book.pages) == 2
    assert len(book.pages[0].Sentence) == 10
    assert len(book.pages[1].Sentence) == 1


def test_overlong_sentence_goes_alone_in_page():
    # 80 words -> 80 / 2.5 = 32s > 30s target, so it overflows a page alone.
    long_text = "word " * 79 + "end."
    doc = build_document(paragraph(long_text), paragraph("Short."))
    book = paginator.paginate(doc, "Book")

    assert len(book.pages) == 2
    assert len(book.pages[0].Sentence) == 1
    assert len(book.pages[1].Sentence) == 1


def test_global_timeline_accumulates_across_pages():
    doc = build_document(
        paragraph("One two three four five."),  # 5 words -> 2s
        paragraph("Six seven eight nine ten."),  # 5 words -> 2s
    )
    book = paginator.paginate(doc, "Book")

    s1, s2 = book.pages[0].Sentence
    assert s1.start == 0.0
    assert s1.end == 2.0
    assert s2.start == 2.0
    assert s2.end == 4.0
    assert s1.nextSegmentCode == s2.segmentCode


def test_segment_and_page_codes_are_chained():
    doc = build_document(paragraph("Alpha."), heading(1, "Beta"), paragraph("Gamma."))
    book = paginator.paginate(doc, "Book")

    p1, p2 = book.pages
    assert p1.nextPageCode == p2.pageCode
    assert p2.nextPageCode == ""

    for i in range(len(p1.Sentence) - 1):
        assert p1.Sentence[i].nextSegmentCode == p1.Sentence[i + 1].segmentCode
    assert p1.Sentence[-1].nextSegmentCode == p2.Sentence[0].segmentCode


def test_txt_style_flat_text_nodes_are_paginated():
    doc = build_document(text_node("Line one."), text_node("Line two."))
    book = paginator.paginate(doc, "Book")

    assert len(book.pages[0].Sentence) == 2
    assert book.pages[0].Sentence[0].text == "Line one."
    assert book.pages[0].Sentence[1].text == "Line two."
