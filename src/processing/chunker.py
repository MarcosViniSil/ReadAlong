import uuid
from dataclasses import dataclass, field

from models.Page import Page
from models.Sentence import Sentence
from models.chunk import Chunk
from models.enum.BookStatus import BookStatus
from processing.paginator import PageData, PaginatedBook


@dataclass
class ChunkData:
    chunk: Chunk
    page: Page
    sentences: list[Sentence] = field(default_factory=list)


class Chunker:

    def chunk_book(
        self,
        paginated: PaginatedBook,
    ) -> list[ChunkData]:

        chunks: list[ChunkData] = []

        for page_data in paginated.pages:
            chunks.extend(
                self._chunk_page(page_data)
            )

        return chunks

    def _chunk_page(
        self,
        page_data: PageData,
    ) -> list[ChunkData]:

        chunks: list[ChunkData] = []

        sequence = 0

        for sentence in page_data.sentences:

            if not self._is_spoken(sentence):
                continue

            sequence += 1

            chunks.append(
                self._make_chunk(
                    page_data.page,
                    sequence,
                    [sentence],
                )
            )

        return chunks

    def _make_chunk(
        self,
        page: Page,
        sequence: int,
        sentences: list[Sentence],
    ) -> ChunkData:

        chunk = Chunk(
            id=str(uuid.uuid4()),
            page_id=page.id,
            sequence=sequence,
            text=" ".join(
                s.text
                for s in sentences
            ).strip(),
            status=BookStatus.PENDING,
            created_at=None,
            updated_at=None,
        )

        for sentence in sentences:
            sentence.audio = None
            sentence.id = chunk.id

        return ChunkData(
            chunk=chunk,
            page=page,
            sentences=list(sentences),
        )

    def _is_spoken(
        self,
        sentence: Sentence,
    ) -> bool:

        return bool(sentence.text)
