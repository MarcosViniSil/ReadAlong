import json
import re
from pathlib import Path

from processing.paginator import PaginatedBook

DEFAULT_OUTPUT_DIR = Path("audio")


def book_code(title: str) -> str:
    """Slug used for the book JSON filename, derived from the book title."""
    code = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()
    return code or "book"


def page_code(sequence: int) -> str:
    return f"P{sequence:03d}"


def _sentence_dict(sentence) -> dict:
    return {
        "sentenceType": sentence.sentenceType.value,
        "text": sentence.text,
        "segmentCode": sentence.segmentCode,
        "nextSegmentCode": sentence.nextSegmentCode,
        "start": sentence.start,
        "end": sentence.end,
        "duration": sentence.duration,
    }


def serialize_book(paginated: PaginatedBook) -> dict:
    """Convert a PaginatedBook into the JSON payload consumed by the frontend.

    Timeline fields (start/end/duration) are the global offsets on the
    single concatenated audio file.
    """
    pages = []
    total = len(paginated.pages)
    for index, page_data in enumerate(paginated.pages):
        sequence = page_data.page.sequence
        sentences = [_sentence_dict(s) for s in page_data.sentences]
        pages.append({
            "pageCode": page_code(sequence),
            "nextPageCode": page_code(sequence + 1) if index + 1 < total else "",
            "sequence": sequence,
            "start": sentences[0]["start"] if sentences else 0.0,
            "end": sentences[-1]["end"] if sentences else 0.0,
            "sentences": sentences,
        })

    duration = pages[-1]["end"] if pages else 0.0

    return {
        "bookName": paginated.book.title,
        "bookCode": book_code(paginated.book.title),
        "audioFile": paginated.audio_file,
        "duration": duration,
        "pages": pages,
    }


def write_book_json(paginated: PaginatedBook, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """Serialize the book and write it to <output_dir>/<bookCode>.json."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{book_code(paginated.book.title)}.json"
    path.write_text(
        json.dumps(serialize_book(paginated), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
