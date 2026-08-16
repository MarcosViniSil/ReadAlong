import re
from dataclasses import dataclass, field

from models.Book import Book
from models.Node import Node
from models.Page import Page
from models.Sentence import Sentence
from models.SentenceType import SentenceType
from models.enum.NodeType import NodeType


@dataclass
class ReadingUnit:
    text: str
    sentence_type: SentenceType
    metadata: dict = field(default_factory=dict)
    duration: float = 0.0

    @property
    def is_spoken(self) -> bool:
        return self.sentence_type == SentenceType.TEXT and bool(self.text)


class Paginator:
    WORDS_PER_SECOND = 2.5
    TARGET_PAGE_DURATION = 30.0

    _BLOCK_TYPES = {
        NodeType.PARAGRAPH,
        NodeType.LIST_ITEM,
        NodeType.QUOTE,
        NodeType.CELL,
    }

    _SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")

    def paginate(self, root: Node, book_name: str) -> Book:
        units: list[ReadingUnit] = []
        self._collect_units(root, units)
        pages = self._build_pages(units)
        return self._to_book(book_name, pages)

    # ------------------------------------------------------------------ #
    # Step A: collect reading units from the node tree (pre-order, keeps  #
    # reading order). Spoken units are sentences; IMAGE/FORMULA/TABLE are #
    # non-spoken markers kept for transcription.                          #
    # ------------------------------------------------------------------ #
    def _collect_units(self, node: Node, units: list[ReadingUnit]) -> None:
        node_type = node.type

        if node_type in self._BLOCK_TYPES:
            text = self._clean(self._node_text(node))
            if text:
                for sentence in self._split_sentences(text):
                    units.append(self._spoken_unit(sentence))
            return

        if node_type == NodeType.HEADING:
            text = self._clean(self._node_text(node))
            if text:
                units.append(ReadingUnit(
                    text=text,
                    sentence_type=SentenceType.TEXT,
                    metadata={"level": node.metadata.get("level", 1)},
                    duration=self._estimate_duration(text),
                ))
            return

        if node_type == NodeType.CODE:
            text = self._clean(self._node_text(node))
            if text:
                units.append(self._spoken_unit(text, code=True))
            return

        if node_type == NodeType.TABLE:
            units.append(ReadingUnit(
                text=self._flatten_table(node),
                sentence_type=SentenceType.TABLE,
            ))
            return

        if node_type == NodeType.IMAGE:
            units.append(ReadingUnit(
                text="",
                sentence_type=SentenceType.IMAGE,
                metadata={"src": node.metadata.get("src")},
            ))
            return

        if node_type == NodeType.FORMULA:
            units.append(ReadingUnit(
                text="",
                sentence_type=SentenceType.LATEX,
                metadata={"raw": node.metadata.get("raw")},
            ))
            return

        if node_type == NodeType.TEXT:
            text = self._clean(node.text)
            if text:
                for sentence in self._split_sentences(text):
                    units.append(self._spoken_unit(sentence))
            return

        # Containers (DOCUMENT/CHAPTER/SECTION/LIST/ROW/...): recurse.
        for child in node.children:
            self._collect_units(child, units)

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
    # Step C: materialize Book -> Page -> Sentence with global timeline.  #
    # ------------------------------------------------------------------ #
    def _to_book(self, book_name: str, pages: list[list[ReadingUnit]]) -> Book:
        book = Book(
            bookName=book_name,
            bookCode=self._book_code(book_name),
            pages=[],
        )
        cursor = 0.0
        segment_counter = 0
        previous_sentence: Sentence | None = None

        for page_index, page_units in enumerate(pages):
            page_code = f"P{page_index + 1:03d}"
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
                )
                # Chain segments across the whole book (single final audio),
                # so the last sentence of a page links to the first of the next.
                if previous_sentence is not None:
                    previous_sentence.nextSegmentCode = sentence.segmentCode
                sentences.append(sentence)
                previous_sentence = sentence
                cursor = end

            book.pages.append(Page(
                pageCode=page_code,
                audioFile="",
                Sentence=sentences,
                nextPageCode="",
            ))

        for i in range(len(book.pages) - 1):
            book.pages[i].nextPageCode = book.pages[i + 1].pageCode

        return book

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #
    def _spoken_unit(self, text: str, code: bool = False) -> ReadingUnit:
        return ReadingUnit(
            text=text,
            sentence_type=SentenceType.TEXT,
            metadata={"code": True} if code else {},
            duration=self._estimate_duration(text),
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

    @staticmethod
    def _book_code(book_name: str) -> str:
        code = re.sub(r"[^A-Za-z0-9]+", "-", book_name).strip("-").lower()
        return code or "book"
