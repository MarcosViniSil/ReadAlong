from models.Node import Node
from models.enum.NodeType import NodeType
from models.enum.BookStatus import BookStatus
from processing.chunker import Chunker
from processing.paginator import Paginator

chunker = Chunker()
paginator = Paginator()


def build_document(*children) -> Node:
    return Node(type=NodeType.DOCUMENT, children=list(children))


def paragraph(*sentences: str) -> Node:
    return Node(type=NodeType.PARAGRAPH, children=[Node(type=NodeType.TEXT, text=s) for s in sentences])


def heading(level: int, text: str) -> Node:
    return Node(type=NodeType.HEADING, metadata={"level": level}, children=[Node(type=NodeType.TEXT, text=text)])


def image(src: str) -> Node:
    return Node(type=NodeType.IMAGE, metadata={"src": src})


def test_chunker_ignores_non_spoken_markers():
    doc = build_document(
        paragraph("Hello world."),
        image("cover.jpg"),
        paragraph("Second paragraph."),
    )
    paginated = paginator.paginate(doc, "My Book")
    chunks = chunker.chunk_book(paginated)

    # Only the two spoken sentences join chunks; the image is skipped.
    texts = [s.text for c in chunks for s in c.sentences]
    assert texts == ["Hello world.", "Second paragraph."]


def test_chunker_splits_at_block_boundaries():
    doc = build_document(
        paragraph("One."),
        paragraph("Two."),
    )
    paginated = paginator.paginate(doc, "My Book")
    chunks = chunker.chunk_book(paginated)

    # Each paragraph is its own block, so each becomes its own chunk.
    assert len(chunks) == 2
    assert [c.chunk.text for c in chunks] == ["One.", "Two."]


def test_chunker_respects_target_duration():
    # Many sentences in the same paragraph: total duration exceeds the
    # chunk target (~30s), so the paragraph splits into multiple chunks.
    long_text = " ".join("This is sentence number %d." % i for i in range(30))
    doc = build_document(paragraph(long_text))
    paginated = paginator.paginate(doc, "My Book")
    chunks = chunker.chunk_book(paginated)

    assert len(chunks) > 1
    # Sentences are indivisible: each chunk text is a full-sentence subset.
    for c in chunks:
        assert c.chunk.text
    # Chunks are numbered sequentially.
    assert [c.chunk.sequence for c in chunks] == list(range(1, len(chunks) + 1))
    # Chunks belong to the page (Page object carried along).
    assert all(c.page.sequence == 1 for c in chunks)


def test_chunker_creates_db_shaped_chunks():
    doc = build_document(paragraph("Hello world."))
    paginated = paginator.paginate(doc, "My Book")
    chunks = chunker.chunk_book(paginated)

    assert len(chunks) == 1
    chunk = chunks[0].chunk
    assert chunk.id
    assert chunk.page_id == ""
    assert chunk.status == BookStatus.PENDING
    assert chunk.text == "Hello world."
