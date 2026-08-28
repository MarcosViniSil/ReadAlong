import re
from dataclasses import dataclass, field

from models.Book import Book
from models.Node import Node
from models.Page import Page
from models.Sentence import Sentence
from models.SentenceType import SentenceType
from models.enum.BookStatus import BookStatus
from models.enum.NodeType import NodeType
from models.enum.languages import Languages


@dataclass
class ReadingUnit:
    text: str
    sentence_type: SentenceType
    metadata: dict = field(default_factory=dict)
    duration: float = 0.0
    block_type: str = ""
    block_code: str = ""

    @property
    def is_spoken(self) -> bool:
        return self.sentence_type == SentenceType.TEXT and bool(self.text)


@dataclass
class PageData:
    page: Page
    sentences: list[Sentence]


@dataclass
class PaginatedBook:
    book: Book
    pages: list[PageData]
    audio_file: str = ""


class Paginator:
    WORDS_PER_SECOND = 3
    TARGET_PAGE_DURATION = 8 * 60 

    _BLOCK_TYPES = {
        NodeType.PARAGRAPH,
        NodeType.LIST_ITEM,
        NodeType.QUOTE,
        NodeType.CELL,
    }

    _SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")

    def paginate(self, root: Node, book_name: str) -> PaginatedBook:
        units: list[ReadingUnit] = []
        self._collect_units(root, units)
        pages = self._build_pages(units)
        return self._to_book(book_name, pages)

    # ------------------------------------------------------------------  #
    # Step A: collect reading units from the node tree (pre-order, keeps  #
    # reading order). Spoken units are sentences; IMAGE/FORMULA/TABLE are #
    # non-spoken markers kept for transcription. Each source block node   #
    # gets its own block_code so the semantic tree survives pagination.   #
    # ------------------------------------------------------------------  #
    def _collect_units(self, node: Node, units: list[ReadingUnit], counter: list[int] | None = None) -> None:
        if counter is None:
            counter = [0]
        node_type = node.type

        if node_type in self._BLOCK_TYPES:
            text = self._clean(self._node_text(node))
            if text:
                block = self._next_block(counter, node_type.value)
                for sentence in self._split_sentences(text):
                    units.append(self._spoken_unit(sentence, block_type=block[0], block_code=block[1]))
            return

        if node_type == NodeType.HEADING:
            text = self._clean(self._node_text(node))
            if text:
                block_type, block_code = self._next_block(counter, node_type.value)
                units.append(ReadingUnit(
                    text=text,
                    sentence_type=SentenceType.TEXT,
                    metadata={"level": node.metadata.get("level", 1)},
                    duration=self._estimate_duration(text),
                    block_type=block_type,
                    block_code=block_code,
                ))
            return

        if node_type == NodeType.CODE:
            text = self._clean(self._node_text(node))
            if text:
                block_type, block_code = self._next_block(counter, node_type.value)
                units.append(self._spoken_unit(text, code=True, block_type=block_type, block_code=block_code))
            return

        if node_type == NodeType.TABLE:
            block_type, block_code = self._next_block(counter, node_type.value)
            units.append(ReadingUnit(
                text=self._flatten_table(node),
                sentence_type=SentenceType.TABLE,
                block_type=block_type,
                block_code=block_code,
            ))
            return

        if node_type == NodeType.IMAGE:
            block_type, block_code = self._next_block(counter, node_type.value)
            units.append(ReadingUnit(
                text="",
                sentence_type=SentenceType.IMAGE,
                metadata={"src": node.metadata.get("src")},
                block_type=block_type,
                block_code=block_code,
            ))
            return

        if node_type == NodeType.FORMULA:
            block_type, block_code = self._next_block(counter, node_type.value)
            units.append(ReadingUnit(
                text="",
                sentence_type=SentenceType.LATEX,
                metadata={"raw": node.metadata.get("raw")},
                block_type=block_type,
                block_code=block_code,
            ))
            return

        if node_type == NodeType.TEXT:
            text = self._clean(node.text)
            if text:
                block_type, block_code = self._next_block(counter, NodeType.PARAGRAPH.value)
                for sentence in self._split_sentences(text):
                    units.append(self._spoken_unit(sentence, block_type=block_type, block_code=block_code))
            return

        # Containers (DOCUMENT/CHAPTER/SECTION/LIST/ROW/...): recurse.
        for child in node.children:
            self._collect_units(child, units, counter)

    # ------------------------------------------------------------------ #
    # Step B: group units into pages by estimated duration.               #
    # ------------------------------------------------------------------ #
    def _build_pages(self, units: list[ReadingUnit]) -> list[list[ReadingUnit]]:
        pages: list[list[ReadingUnit]] = []
        current: list[ReadingUnit] = []
        duration = 0.0

        for unit in units:
            # Structural break: heading level 1 starts a new page.
            if unit.metadata.get("level") == 1 and unit.sentence_type == SentenceType.TEXT:
                if current:
                    pages.append(current)
                    current = []
                    duration = 0.0
                current.append(unit)
                duration += unit.duration
                continue

            # Non-spoken markers enter the page without consuming duration.
            if not unit.is_spoken:
                current.append(unit)
                continue

            if duration + unit.duration > self.TARGET_PAGE_DURATION and current:
                pages.append(current)
                current = []
                duration = 0.0

            current.append(unit)
            duration += unit.duration

        if current:
            pages.append(current)

        return pages

    # ------------------------------------------------------------------ #
    # Step C: materialize DB-shaped Book/Page plus sentence trees.        #
    # ------------------------------------------------------------------ #
    def _to_book(self, book_name: str, pages: list[list[ReadingUnit]]) -> PaginatedBook:
        book = Book(
            title=book_name,
            author="",
            book_url="",
            language=Languages.ENGLISH,
            status=BookStatus.PROCESSING,
            total_pages=len(pages),
            completed_pages=0,
        )
        page_datas: list[PageData] = []
        cursor = 0.0
        segment_counter = 0
        previous_sentence: Sentence | None = None

        for page_index, page_units in enumerate(pages):
            sequence = page_index + 1
            page_code = f"P{sequence:03d}"
            sentences: list[Sentence] = []

            for unit in page_units:
                segment_counter += 1
                start = cursor
                end = start + unit.duration
                sentence = Sentence(
                    sentenceType=unit.sentence_type,
                    pageCode=page_code,
                    text=unit.text,
                    segmentCode=f"S{segment_counter:04d}",
                    duration=unit.duration,
                    start=start,    
                    end=end,
                    nextSegmentCode="",
                    block_type=unit.block_type,
                    block_code=unit.block_code,
                    metadata=unit.metadata,
                )
                # Chain segments across the whole book (single final audio),
                # so the last sentence of a page links to the first of the next.
                if previous_sentence is not None:
                    previous_sentence.nextSegmentCode = sentence.segmentCode
                sentences.append(sentence)
                previous_sentence = sentence
                cursor = end

            page = Page(
                id="",
                processing_run_id="",
                sequence=sequence,
                page_url="",
                sentence_count=len(sentences),
                status=BookStatus.COMPLETED,
                created_at=None,
                updated_at=None,
            )
            page_datas.append(PageData(page=page, sentences=sentences))

        return PaginatedBook(book=book, pages=page_datas)

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #
    def _next_block(self, counter: list[int], block_type: str) -> tuple[str, str]:
        counter[0] += 1
        return block_type, f"B{counter[0]:04d}"

    def _spoken_unit(self, text: str, code: bool = False, block_type: str = "", block_code: str = "") -> ReadingUnit:
        return ReadingUnit(
            text=text,
            sentence_type=SentenceType.TEXT,
            metadata={"code": True} if code else {},
            duration=self._estimate_duration(text),
            block_type=block_type,
            block_code=block_code,
        )

    def _node_text(self, node: Node) -> str:
        if node.text:
            return node.text
        return " ".join(self._node_text(child) for child in node.children).strip()

    def _split_sentences(self, text: str) -> list[str]:
        return [part.strip() for part in self._SENTENCE_SPLIT.split(text) if part.strip()]

    def _estimate_duration(self, text: str) -> float:
        return len(text.split()) / self.WORDS_PER_SECOND

    def _clean(self, text: str) -> str:
        return " ".join(text.split())

    def _flatten_table(self, node: Node) -> str:
        rows = []
        for row in node.children:
            cells = []
            for cell in row.children:
                cells.append(self._clean(self._node_text(cell)))
            if cells:
                rows.append(" | ".join(cells))
        return " ; ".join(rows)
