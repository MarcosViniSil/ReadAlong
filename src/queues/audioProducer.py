"""Build the queue message (job) for one chunk.

The message is self-contained: the worker only needs this JSON to
synthesize audio. ``chunk_id`` is the id that identifies the text inside
the book — the worker echoes it back so the orchestrator can map the
response to the right page/sentences.
"""
import uuid

from export.bookExporter import page_code
from models.Book import Book
from models.enum.languages import Languages
from processing.chunker import ChunkData


def build_chunk_message(book: Book, chunk_data: ChunkData) -> dict:
    """Serialize a chunk into the job message sent to the audio worker."""
    language = book.language.value if isinstance(book.language, Languages) else str(book.language)

    return {
        "id": str(uuid.uuid4()),
        "type": "generate_audio",
        "chunk_id": chunk_data.chunk.id,
        "book_id": book.id or "",
        "page_id": chunk_data.page.id or "",
        "page_code": page_code(chunk_data.page.sequence),
        "sequence": chunk_data.chunk.sequence,
        "book_title": book.title,
        "language": language,
        "content": chunk_data.chunk.text,
        "sentences": [
            {"segmentCode": s.segmentCode, "text": s.text}
            for s in chunk_data.sentences
        ],
    }


def publish_book_chunks(audio_queue, book: Book, chunk_datas: list[ChunkData]) -> list[dict]:
    """Build and publish one message per chunk, returning the messages.

    The returned list lets the pipeline collect the chunk_ids it must
    wait for in wait_for_results.
    """
    messages = [build_chunk_message(book, chunk_data) for chunk_data in chunk_datas]
    if messages:
        audio_queue.publish_jobs(messages)
    return messages
