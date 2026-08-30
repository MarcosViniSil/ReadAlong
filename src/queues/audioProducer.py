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




def publish_messages(audio_queue, messages) -> list[dict]:
    """Build and publish one message per chunk, returning the messages.

    The returned list lets the pipeline collect the chunk_ids it must
    wait for in wait_for_results.
    """
    if messages:
        audio_queue.publish_jobs(messages)
    return messages
