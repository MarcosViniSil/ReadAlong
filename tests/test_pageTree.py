import json

from export.pageTree import serialize_page, write_page_jsons
from models.Node import Node
from models.enum.NodeType import NodeType
from processing.paginator import Paginator


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


def test_serialize_page_shape_with_heading_paragraph_image():
    root = build_document(
        heading(1, "Chapter One"),
        paragraph("First. Second."),
        image("cover.jpg"),
    )
    paginated = Paginator().paginate(root, "Book")
    tree = serialize_page(paginated.pages[0])

    assert tree["id"] == "P001"
    assert tree["type"] == "page"
    assert tree["content"] == "Chapter One"  # first heading becomes the page title
    assert tree["metadata"] == {"sequence": 1, "pageCode": "P001"}
    assert "audio" not in tree  # page is a container, not spoken
    assert tree["segmentCode"] is None
    assert tree["nextSegmentCode"] is None
    assert tree["nextPageCode"] == ""

    children = tree["children"]
    assert [c["type"] for c in children] == ["heading", "paragraph", "image"]

    heading_node = children[0]
    assert heading_node["content"] == "Chapter One"
    assert heading_node["metadata"] == {"level": 1}
    assert heading_node["children"] == []
    assert heading_node["audio"] == {"chunk_id": None, "start": None, "end": None, "duration": None, "words": []}
    assert heading_node["segmentCode"] is None
    assert heading_node["nextSegmentCode"] is None

    paragraph_node = children[1]
    assert paragraph_node["content"] is None
    assert "audio" not in paragraph_node  # container carries no audio of its own
    sentence_nodes = paragraph_node["children"]
    assert [s["type"] for s in sentence_nodes] == ["sentence", "sentence"]
    assert sentence_nodes[0]["content"] == "First."
    assert [s["id"] for s in sentence_nodes] == ["S0002", "S0003"]
    assert sentence_nodes[0]["metadata"]["sentenceType"] == "text"
    assert [s["segmentCode"] for s in sentence_nodes] == ["S0002", "S0003"]
    assert sentence_nodes[0]["nextSegmentCode"] == "S0003"
    # Spoken sentences carry the audio placeholder; both are TEXT.
    assert sentence_nodes[0]["audio"] == {"chunk_id": None, "start": None, "end": None, "duration": None, "words": []}
    assert sentence_nodes[1]["audio"] == {"chunk_id": None, "start": None, "end": None, "duration": None, "words": []}
    # The trailing image unit still gets a segment code in the chain.
    assert sentence_nodes[1]["nextSegmentCode"] == "S0004"
    assert "nextSegmentCode" not in sentence_nodes[0]["metadata"]

    image_node = children[2]
    assert image_node["content"] is None
    assert "audio" not in image_node  # image is not spoken
    assert image_node["metadata"] == {"src": "cover.jpg"}
    assert image_node["children"] == []
    assert image_node["segmentCode"] is None
    assert image_node["nextSegmentCode"] is None


def test_adjacent_paragraphs_stay_separate_blocks():
    root = build_document(paragraph("One."), paragraph("Two."))
    paginated = Paginator().paginate(root, "Book")
    tree = serialize_page(paginated.pages[0])

    paragraph_blocks = [c for c in tree["children"] if c["type"] == "paragraph"]
    assert len(paragraph_blocks) == 2
    assert paragraph_blocks[0]["children"][0]["content"] == "One."
    assert paragraph_blocks[1]["children"][0]["content"] == "Two."


def test_page_without_heading_has_null_content():
    root = build_document(paragraph("Some text."))
    tree = serialize_page(Paginator().paginate(root, "Book").pages[0])

    assert tree["content"] is None


def test_formula_and_table_blocks():
    root = build_document(
        formula(r"\frac{a}{b}"),
        paragraph("Text."),
    )
    paginated = Paginator().paginate(root, "Book")
    tree = serialize_page(paginated.pages[0])

    assert [c["type"] for c in tree["children"]] == ["latex", "paragraph"]
    assert tree["children"][0]["content"] is None
    assert tree["children"][0]["metadata"] == {"raw": r"\frac{a}{b}"}


def test_list_items_group_into_list_block():
    def list_item(text: str) -> Node:
        return Node(type=NodeType.LIST_ITEM, children=[text_node(text)])

    root = build_document(
        Node(type=NodeType.LIST, children=[list_item("First item."), list_item("Second item.")])
    )
    paginated = Paginator().paginate(root, "Book")
    tree = serialize_page(paginated.pages[0])

    assert len(tree["children"]) == 1
    list_node = tree["children"][0]
    assert list_node["type"] == "list"
    item_nodes = list_node["children"]
    assert [c["type"] for c in item_nodes] == ["list_item", "list_item"]
    assert item_nodes[0]["children"][0]["content"] == "First item."
    assert item_nodes[1]["children"][0]["content"] == "Second item."


def test_write_page_jsons_writes_one_file_per_page(tmp_path):
    root = build_document(
        paragraph("First page text."),
        heading(1, "Second Page"),
        paragraph("More."),
    )
    paginated = Paginator().paginate(root, "My Book")

    paths = write_page_jsons(paginated, tmp_path)

    assert len(paths) == 2
    assert paths[0] == tmp_path / "my-book" / "pages" / "P001.json"
    assert paths[1] == tmp_path / "my-book" / "pages" / "P002.json"

    first = json.loads(paths[0].read_text(encoding="utf-8"))
    assert first["type"] == "page"
    assert first["id"] == "P001"
    assert first["content"] is None
    assert first["nextPageCode"] == "P002"

    second = json.loads(paths[1].read_text(encoding="utf-8"))
    assert second["id"] == "P002"
    assert second["content"] == "Second Page"
    assert second["nextPageCode"] == ""
