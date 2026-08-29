"""Per-page semantic JSON: page -> blocks -> sentences.

Each page becomes a recursive tree node {id, type, segmentCode,
nextSegmentCode, content, metadata, children} plus a top-level
nextPageCode on the page itself. Segment codes are only filled on
sentence nodes; pages and blocks carry null. The ``audio`` key appears
as null on every node with speakable content (sentences, headings,
code, tables, list items, quote sentences) and is replaced by real
timings once the TTS merge runs; containers (page, paragraph, list,
quote, ...) and empty markers (image, latex) omit it. The ``id`` of a
spoken node (sentences, headings, code, tables) is the chunk uuid the
chunker stamps on ``sentence.id`` — the same id persisted in the
``chunks`` table — falling back to ``segmentCode``/``block_code`` when
no chunk exists yet; pure containers use their ``block_code``. Block grouping comes from the block_code the paginator
stamps on every Sentence, so paragraph boundaries survive pagination.
"""
import json
from pathlib import Path

from export.bookExporter import DEFAULT_OUTPUT_DIR, book_code, page_code
from processing.paginator import PaginatedBook, PageData

_BLOCK_TYPE_TO_JSON_TYPE = {
    "Paragraph": "paragraph",
    "Text": "paragraph",
    "Cell": "paragraph",
    "Heading": "heading",
    "Quote": "quote",
    "Code": "code",
    "Image": "image",
    "Formula": "latex",
    "Table": "table",
}

_SENTENCE_TYPE_TO_BLOCK_TYPE = {
    "text": "Paragraph",
    "image": "Image",
    "latex": "Formula",
    "table": "Table",
}


def _node(node_id: str, node_type: str, content, metadata: dict, children: list,
          segment_code: str | None = None, next_segment_code: str | None = None,
          spoken: bool | None = None) -> dict:
    node = {
        "id": node_id,
        "type": node_type,
        "segmentCode": segment_code,
        "nextSegmentCode": next_segment_code,
        "content": content,
        "metadata": metadata,
        "children": children,
    }
    # Every node with speakable content gets an ``audio`` slot, null until
    # the TTS merge fills it. Containers pass spoken=False to stay without.
    if spoken is None:
        spoken = content is not None
    if spoken:
        node["audio"] = None
    return node


def _sentence_node(sentence) -> dict:
    # The chunker stamps the chunk uuid (the id persisted in the ``chunks``
    # table) onto every spoken sentence; that uuid is the node's stable
    # identity. ``audio`` stays null here — the TTS merge fills it later.
    print(sentence)
    return _node(
        sentence.id or sentence.segmentCode,
        "sentence",
        sentence.text or None,
        {"sentenceType": sentence.sentenceType.value},
        [],
        segment_code=sentence.segmentCode,
        next_segment_code=sentence.nextSegmentCode or None,
    )


def _json_type(block_type: str) -> str:
    return _BLOCK_TYPE_TO_JSON_TYPE.get(block_type, block_type.lower())


def _group_blocks(sentences: list) -> list[dict]:
    """Group the flat sentence list into blocks.

    Consecutive sentences sharing a block_code form one block; a run of
    list items is wrapped into a single "list" container whose items keep
    their own block boundaries.
    """
    blocks: list[dict] = []
    for sentence in sentences:
        block_type = sentence.block_type or _SENTENCE_TYPE_TO_BLOCK_TYPE.get(
            sentence.sentenceType.value, sentence.sentenceType.value
        )

        if block_type == "ListItem":
            if blocks and blocks[-1]["type"] == "list":
                current = blocks[-1]
                if current["items"] and current["items"][-1]["block_code"] == sentence.block_code:
                    current["items"][-1]["sentences"].append(sentence)
                else:
                    current["items"].append({"block_code": sentence.block_code, "sentences": [sentence]})
            else:
                blocks.append({
                    "type": "list",
                    "items": [{"block_code": sentence.block_code, "sentences": [sentence]}],
                })
            continue

        if blocks and blocks[-1].get("block_code") == sentence.block_code:
            blocks[-1]["sentences"].append(sentence)
        else:
            blocks.append({
                "type": block_type,
                "block_code": sentence.block_code,
                "sentences": [sentence],
            })
    return blocks


def _serialize_block(block: dict) -> dict:
    block_type = block["type"]

    if block_type == "list":
        children = [_item_node(item) for item in block["items"]]
        first_item = block["items"][0]
        return _node(first_item["block_code"], "list", None, {}, children)

    sentences = block["sentences"]
    first = sentences[0]
    code = block["block_code"]

    if block_type == "Heading":
        return _node(first.id or code, "heading",
                     " ".join(s.text for s in sentences if s.text).strip(),
                     {"level": first.metadata.get("level", 1)}, [])

    if block_type == "Code":
        return _node(first.id or code, "code",
                     " ".join(s.text for s in sentences if s.text).strip(), {}, [])

    if block_type == "Image":
        return _node(code, "image", None, {"src": first.metadata.get("src")}, [])

    if block_type == "Formula":
        return _node(code, "latex", None, {"raw": first.metadata.get("raw")}, [])

    if block_type == "Table":
        return _node(first.id or code, "table", first.text, {}, [])

    if block_type == "Quote":
        return _node(code, "quote", None, {}, [_sentence_node(s) for s in sentences])

    return _node(code, _json_type(block_type), None, {}, [_sentence_node(s) for s in sentences])


def _item_node(item: dict) -> dict:
    return _node(item["block_code"], "list_item", None, {}, [_sentence_node(s) for s in item["sentences"]])


def serialize_page(page_data: PageData, next_page_code: str = "") -> dict:
    """Build the semantic JSON tree for a single page.

    ``next_page_code`` is the code of the following page ("" for the last
    page of the book); the caller computes it from the full paginated book.
    """
    blocks = _group_blocks(page_data.sentences)
    children = [_serialize_block(b) for b in blocks]

    title = children[0]["content"] if children and children[0]["type"] == "heading" else None

    node = _node(
        page_code(page_data.page.sequence),
        "page",
        title,
        {
            "sequence": page_data.page.sequence,
            "pageCode": page_code(page_data.page.sequence),
        },
        children,
        spoken=False,
    )
    node["nextPageCode"] = next_page_code
    return node


def write_page_jsons(paginated: PaginatedBook, output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    """Write one JSON file per page to <output_dir>/<bookCode>/pages/."""
    pages_dir = Path(output_dir) / book_code(paginated.book.title) / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for index, page_data in enumerate(paginated.pages):
        next_page_code = (
            page_code(paginated.pages[index + 1].page.sequence)
            if index + 1 < len(paginated.pages)
            else ""
        )
        path = pages_dir / f"{page_code(page_data.page.sequence)}.json"
        path.write_text(
            json.dumps(serialize_page(page_data, next_page_code), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        paths.append(path)
    return paths
