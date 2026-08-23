from models.Node import Node
from models.SentenceType import SentenceType
from models.enum.BookStatus import BookStatus
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


def test_paginate_builds_db_book_and_pages():
    doc = build_document(paragraph("Hello world."))
    paginated = paginator.paginate(doc, "My Book")

    assert paginated.book.title == "My Book"
    assert paginated.book.total_pages == 1
    assert paginated.book.status == BookStatus.PROCESSING

    page_data = paginated.pages[0]
    assert page_data.page.sequence == 1
    assert page_data.page.text == "Hello world."
    assert page_data.page.sentence_count == 1
    assert page_data.page.status == BookStatus.COMPLETED

    assert len(page_data.sentences) == 1
    assert page_data.sentences[0].text == "Hello world."
    assert page_data.sentences[0].sentenceType == SentenceType.TEXT
    assert page_data.sentences[0].pageCode == "P001"


def test_paragraph_is_split_into_sentences():
    doc = build_document(paragraph("First sentence. Second sentence! Third?"))
    paginated = paginator.paginate(doc, "Book")

    texts = [s.text for s in paginated.pages[0].sentences]
    assert texts == ["First sentence.", "Second sentence!", "Third?"]
    assert paginated.pages[0].page.sentence_count == 3


def test_heading_becomes_spoken_sentence_with_level():
    doc = build_document(heading(1, "Introduction"))
    paginated = paginator.paginate(doc, "Book")

    sentence = paginated.pages[0].sentences[0]
    assert sentence.text == "Introduction"
    assert sentence.sentenceType == SentenceType.TEXT
    assert sentence.metadata["level"] == 1


def test_heading_level_1_forces_page_break():
    doc = build_document(
        paragraph("Some intro text."),
        heading(1, "Chapter One"),
        paragraph("Chapter body."),
    )
    paginated = paginator.paginate(doc, "Book")

    assert len(paginated.pages) == 2
    assert paginated.pages[0].sentences[0].text == "Some intro text."
    assert paginated.pages[1].sentences[0].text == "Chapter One"
    assert paginated.pages[1].sentences[1].text == "Chapter body."
    assert paginated.pages[0].page.sequence == 1
    assert paginated.pages[1].page.sequence == 2


def test_image_formula_table_become_non_spoken_markers():
    doc = build_document(
        paragraph("Before the figure."),
        image("cover.jpg"),
        formula(r"\frac{a}{b}"),
        table([["h1", "h2"], ["a", "b"]]),
        paragraph("After the figure."),
    )
    paginated = paginator.paginate(doc, "Book")

    types = [s.sentenceType for s in paginated.pages[0].sentences]
    texts = [s.text for s in paginated.pages[0].sentences]

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
    paginated = paginator.paginate(doc, "Book")

    assert len(paginated.pages) == 2
    assert len(paginated.pages[0].sentences) == 10
    assert len(paginated.pages[1].sentences) == 1


def test_overlong_sentence_goes_alone_in_page():
    # 80 words -> 80 / 2.5 = 32s > 30s target, so it overflows a page alone.
    long_text = "word " * 79 + "end."
    doc = build_document(paragraph(long_text), paragraph("Short."))
    paginated = paginator.paginate(doc, "Book")

    assert len(paginated.pages) == 2
    assert len(paginated.pages[0].sentences) == 1
    assert len(paginated.pages[1].sentences) == 1


def test_global_timeline_accumulates_across_pages():
    doc = build_document(
        paragraph("One two three four five."),  # 5 words -> 2s
        paragraph("Six seven eight nine ten."),  # 5 words -> 2s
    )
    paginated = paginator.paginate(doc, "Book")

    s1, s2 = paginated.pages[0].sentences
    assert s1.start == 0.0
    assert s1.end == 2.0
    assert s2.start == 2.0
    assert s2.end == 4.0
    assert s1.nextSegmentCode == s2.segmentCode


def test_segment_codes_are_chained_across_pages():
    doc = build_document(paragraph("Alpha."), heading(1, "Beta"), paragraph("Gamma."))
    paginated = paginator.paginate(doc, "Book")

    p1, p2 = paginated.pages
    assert p1.page.sequence == 1
    assert p2.page.sequence == 2

    for i in range(len(p1.sentences) - 1):
        assert p1.sentences[i].nextSegmentCode == p1.sentences[i + 1].segmentCode
    assert p1.sentences[-1].nextSegmentCode == p2.sentences[0].segmentCode
    assert p2.sentences[-1].nextSegmentCode == ""


def test_txt_style_flat_text_nodes_are_paginated():
    doc = build_document(text_node("Line one."), text_node("Line two."))
    paginated = paginator.paginate(doc, "Book")

    assert len(paginated.pages[0].sentences) == 2
    assert paginated.pages[0].sentences[0].text == "Line one."
    assert paginated.pages[0].sentences[1].text == "Line two."


def test_sentences_carry_block_type_and_code():
    doc = build_document(
        paragraph("First paragraph."),
        paragraph("Second paragraph."),
        heading(2, "Subtitle"),
        image("pic.png"),
    )
    paginated = paginator.paginate(doc, "Book")
    sentences = paginated.pages[0].sentences

    assert sentences[0].block_type == "Paragraph"
    assert sentences[1].block_type == "Paragraph"
    assert sentences[0].block_code != sentences[1].block_code
    assert sentences[2].block_type == "Heading"
    assert sentences[2].metadata["level"] == 2
    assert sentences[3].block_type == "Image"
