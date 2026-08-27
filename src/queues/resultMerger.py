"""Merge worker responses back into the paginated book.

The final JSON is per-sentence (each spoken sentence carries its own
``audio`` block), but workers respond per-chunk. This module does the
three-stage merge: correlate → shift → inject.
"""
from processing.chunker import ChunkData
from processing.paginator import PageData, PaginatedBook
from models.SentenceType import SentenceType


def merge_results(paginated: PaginatedBook, responses: dict[str, dict],
                  chunks: list[ChunkData]) -> None:
    """Fill each spoken sentence's ``audio`` dict from worker responses.

    Stages:
    1. Correlate: responses are already indexed by chunk_id by the caller
       (out-of-order safe — concurrent workers may reply in any order).
    2. Shift: walk the chunks of each page in sequence order; a per-page
       ``cursor`` accumulates chunk durations, turning each chunk-relative
       start/end into a page-global offset.
    3. Inject: write {chunk_id, start, end, duration, words} onto
       sentence.audio, matching the shape pageTree already serializes.
    """
    # Map each chunk to its owning page (by page sequence) so we can walk
    # every page's chunks in order.
    chunks_by_page_seq: dict[int, list[ChunkData]] = {}
    for chunk_data in chunks:
        chunks_by_page_seq.setdefault(chunk_data.page.sequence, []).append(chunk_data)

    for page_data in paginated.pages:
        _merge_page(page_data, responses, chunks_by_page_seq.get(page_data.page.sequence, []))


def _merge_page(page_data: PageData, responses: dict[str, dict],
                page_chunks: list[ChunkData]) -> None:
    """Shift one page's chunk responses onto the page timeline and inject."""
    cursor = 0.0
    for chunk_data in sorted(page_chunks, key=lambda c: c.chunk.sequence):
        response = responses.get(chunk_data.chunk.id)
        if response is None:
            continue

        # Index this chunk's sentence timings by segmentCode.
        by_segment = {s["segmentCode"]: s for s in response["sentences"]}

        chunk_duration = 0.0
        for sentence in chunk_data.sentences:
            if sentence.sentenceType != SentenceType.TEXT or not sentence.text:
                continue  # non-spoken markers never carry audio

            timings = by_segment.get(sentence.segmentCode)
            if timings is None:
                continue

            sentence.audio = {
                "chunk_id": chunk_data.chunk.id,
                "start": round(cursor + timings["start"], 3),
                "end": round(cursor + timings["end"], 3),
                "duration": timings["duration"],
                "words": [
                    {
                        "text": w["text"],
                        "start": round(cursor + w["start"], 3),
                        "end": round(cursor + w["end"], 3),
                    }
                    for w in timings["words"]
                ],
            }
            chunk_duration = max(chunk_duration, timings["end"])

        cursor += chunk_duration
