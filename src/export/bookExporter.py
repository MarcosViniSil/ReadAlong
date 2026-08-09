import json
from pathlib import Path

from models.Book import Book

DEFAULT_OUTPUT_DIR = Path("audio")


def serialize_book(book: Book) -> dict:
    """Convert a Book into the JSON payload consumed by the frontend.

    Timeline fields (start/end/duration) are the global offsets on the
    single concatenated audio file.
    """
    pages = []
    for page in book.pages:
        sentences = [
            {
                "sentenceType": sentence.sentenceType.value,
                "text": sentence.text,
                "segmentCode": sentence.segmentCode,
                "nextSegmentCode": sentence.nextSegmentCode,
                "start": sentence.start,
                "end": sentence.end,
                "duration": sentence.duration,
            }
            for sentence in page.Sentence
        ]
        pages.append({
            "pageCode": page.pageCode,
            "nextPageCode": page.nextPageCode,
            "start": sentences[0]["start"] if sentences else 0.0,
            "end": sentences[-1]["end"] if sentences else 0.0,
            "sentences": sentences,
        })

    duration = pages[-1]["end"] if pages else 0.0
    audio_file = book.pages[0].audioFile if book.pages else ""

    return {
        "bookName": book.bookName,
        "bookCode": book.bookCode,
        "audioFile": audio_file,
        "duration": duration,
        "pages": pages,
    }


def write_book_json(book: Book, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """Serialize the book and write it to <output_dir>/<bookCode>.json."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{book.bookCode}.json"
    path.write_text(
        json.dumps(serialize_book(book), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
