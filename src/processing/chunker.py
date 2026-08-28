"""Chunking: group a page's spoken sentences into audio job chunks.

A chunk is the unit of work sent to the audio worker. The paginator
already splits a book into pages (~30s of reading); a page can still be
too long for a single TTS request, so we subdivide it into chunks of
about TARGET_CHUNK_DURATION seconds, respecting block boundaries
(paragraphs, headings, ...) and never splitting a sentence.
"""
import uuid
from dataclasses import dataclass, field

from models.Page import Page
from models.Sentence import Sentence
from models.SentenceType import SentenceType
from models.chunk import Chunk
from models.enum.BookStatus import BookStatus
from processing.paginator import PageData, PaginatedBook


@dataclass
class ChunkData:
    chunk: Chunk
    page: Page
    sentences: list[Sentence] = field(default_factory=list)


class Chunker:
    TARGET_CHUNK_DURATION = 30.0

    def chunk_book(self, paginated: PaginatedBook) -> list[ChunkData]:
        """Return one ChunkData per chunk, in reading order across the book."""
        chunks: list[ChunkData] = []
        for page_data in paginated.pages:
            chunks.extend(self._chunk_page(page_data))
        return chunks

    def _chunk_page(self, page_data: PageData) -> list[ChunkData]:
        """Group the spoken sentences of one page into chunks.

        Only spoken sentences (TEXT with text) join a chunk: images,
        formulas and tables are markers with no audio. Sentences are
        indivisible — a chunk never ends in the middle of a sentence. We
        also prefer to cut at block boundaries (block_code changes) so a
        chunk does not tear a paragraph in two when the paragraph fits.
        """
        chunks: list[ChunkData] = []
        current: list[Sentence] = []
        duration = 0.0
        sequence = 0

        for sentence in page_data.sentences:
            if not self._is_spoken(sentence):
                continue

            new_block = current and sentence.block_code != current[-1].block_code
            would_overflow = duration + sentence.duration > self.TARGET_CHUNK_DURATION

            if current and (would_overflow or new_block):
                sequence += 1
                chunks.append(self._make_chunk(page_data.page, sequence, current))
                current = []
                duration = 0.0

            current.append(sentence)
            duration += sentence.duration

        if current:
            sequence += 1
            chunks.append(self._make_chunk(page_data.page, sequence, current))

        return chunks

    def _make_chunk(self, page: Page, sequence: int, sentences: list[Sentence]) -> ChunkData:
        chunk = Chunk(
            id=str(uuid.uuid4()),
            page_id=page.id,
            sequence=sequence,
            text=" ".join(s.text for s in sentences).strip(),
            status=BookStatus.PENDING,
            created_at=None,
            updated_at=None,
        )
        return ChunkData(chunk=chunk, page=page, sentences=list(sentences))

    def _is_spoken(self, sentence: Sentence) -> bool:
        return sentence.sentenceType == SentenceType.TEXT and bool(sentence.text)
