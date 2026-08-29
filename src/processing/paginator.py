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
        return bool(self.text)

    @property
    def is_heading(self) -> bool:
        return "level" in self.metadata

    @property
    def grouping_type(self) -> str:
        if self.is_heading:
            return "heading"

        if self.metadata.get("code"):
            return "code"

        if self.sentence_type == SentenceType.TABLE:
            return "table"

        if self.sentence_type == SentenceType.IMAGE:
            return "image"

        if self.sentence_type == SentenceType.LATEX:
            return "formula"

        if self.sentence_type == SentenceType.TEXT:
            return "text"

        return "other"


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
    WORDS_PER_SECOND = 3.0

    TARGET_PAGE_DURATION = 8 * 60

    TARGET_SEGMENT_DURATION = 10.0
    MIN_SEGMENT_DURATION = 5.0
    MAX_SEGMENT_DURATION = 15.0

    _BLOCK_TYPES = {
        NodeType.PARAGRAPH,
        NodeType.LIST_ITEM,
        NodeType.QUOTE,
        NodeType.CELL,
    }

    _MERGE_RULES = {
        "text": {"text"},
        "list": {"list"},
        "quote": {"quote"},
        "code": set(),
        "table": set(),
        "heading": set(),
        "image": set(),
        "formula": set(),
        "other": set(),
    }

    _SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")

    def paginate(
        self,
        root: Node,
        book_name: str,
    ) -> PaginatedBook:

        units: list[ReadingUnit] = []

        self._collect_units(root, units)

        units = self._group_units_by_duration(units)

        pages = self._build_pages(units)

        return self._to_book(book_name, pages)

    def _collect_units(
        self,
        node: Node,
        units: list[ReadingUnit],
        counter: list[int] | None = None,
    ) -> None:

        if counter is None:
            counter = [0]

        node_type = node.type

        if node_type in self._BLOCK_TYPES:

            text = self._clean(self._node_text(node))

            if text:
                block_type, block_code = self._next_block(
                    counter,
                    node_type.value,
                )

                for sentence in self._split_sentences(text):
                    units.append(
                        self._spoken_unit(
                            sentence,
                            block_type=block_type,
                            block_code=block_code,
                        )
                    )

            return

        if node_type == NodeType.HEADING:

            text = self._clean(self._node_text(node))

            if text:
                block_type, block_code = self._next_block(
                    counter,
                    node_type.value,
                )

                units.append(
                    ReadingUnit(
                        text=text,
                        sentence_type=SentenceType.TEXT,
                        metadata={
                            "level": node.metadata.get(
                                "level",
                                1,
                            ),
                        },
                        duration=self._estimate_duration(text),
                        block_type=block_type,
                        block_code=block_code,
                    )
                )

            return

        if node_type == NodeType.CODE:

            text = self._clean(self._node_text(node))

            if text:
                block_type, block_code = self._next_block(
                    counter,
                    node_type.value,
                )

                units.append(
                    self._spoken_unit(
                        text,
                        code=True,
                        block_type=block_type,
                        block_code=block_code,
                    )
                )

            return

        if node_type == NodeType.TABLE:

            text = self._flatten_table(node)

            block_type, block_code = self._next_block(
                counter,
                node_type.value,
            )

            if text:
                units.append(
                    ReadingUnit(
                        text=text,
                        sentence_type=SentenceType.TABLE,
                        duration=self._estimate_duration(text),
                        block_type=block_type,
                        block_code=block_code,
                    )
                )

            return

        if node_type == NodeType.IMAGE:

            block_type, block_code = self._next_block(
                counter,
                node_type.value,
            )

            units.append(
                ReadingUnit(
                    text="",
                    sentence_type=SentenceType.IMAGE,
                    metadata={
                        "src": node.metadata.get("src"),
                    },
                    block_type=block_type,
                    block_code=block_code,
                )
            )

            return

        if node_type == NodeType.FORMULA:

            block_type, block_code = self._next_block(
                counter,
                node_type.value,
            )

            units.append(
                ReadingUnit(
                    text="",
                    sentence_type=SentenceType.LATEX,
                    metadata={
                        "raw": node.metadata.get("raw"),
                    },
                    block_type=block_type,
                    block_code=block_code,
                )
            )

            return

        if node_type == NodeType.TEXT:

            text = self._clean(node.text)

            if text:
                block_type, block_code = self._next_block(
                    counter,
                    NodeType.PARAGRAPH.value,
                )

                for sentence in self._split_sentences(text):
                    units.append(
                        self._spoken_unit(
                            sentence,
                            block_type=block_type,
                            block_code=block_code,
                        )
                    )

            return

        for child in node.children:
            self._collect_units(
                child,
                units,
                counter,
            )

    def _group_units_by_duration(
        self,
        units: list[ReadingUnit],
    ) -> list[ReadingUnit]:

        result: list[ReadingUnit] = []

        current: list[ReadingUnit] = []
        current_duration = 0.0

        for unit in units:

            if not unit.is_spoken:

                self._flush_group(
                    result,
                    current,
                )

                current = []
                current_duration = 0.0

                result.append(unit)

                continue

            if current and not self._can_merge_units(
                current,
                unit,
            ):

                self._flush_group(
                    result,
                    current,
                )

                current = []
                current_duration = 0.0

            unit_duration = unit.duration

            if not current:

                current = [unit]
                current_duration = unit_duration

                continue

            candidate_duration = current_duration + unit_duration

            if current_duration < self.MIN_SEGMENT_DURATION:

                current.append(unit)
                current_duration = candidate_duration

                continue

            if candidate_duration <= self.MAX_SEGMENT_DURATION:

                current_distance = abs(current_duration - self.TARGET_SEGMENT_DURATION)

                candidate_distance = abs(
                    candidate_duration - self.TARGET_SEGMENT_DURATION
                )

                if candidate_distance < current_distance:

                    current.append(unit)
                    current_duration = candidate_duration

                    continue

            self._flush_group(
                result,
                current,
            )

            current = [unit]
            current_duration = unit_duration

        self._flush_group(
            result,
            current,
        )

        return result

    def _can_merge_units(
        self,
        current: list[ReadingUnit],
        unit: ReadingUnit,
    ) -> bool:

        if not current:
            return True

        current_type = current[0].grouping_type
        next_type = unit.grouping_type

        allowed_types = self._MERGE_RULES.get(
            current_type,
            set(),
        )

        return next_type in allowed_types

    def _flush_group(
        self,
        result: list[ReadingUnit],
        group: list[ReadingUnit],
    ) -> None:

        if not group:
            return

        if len(group) == 1:
            result.append(group[0])
            return

        text = " ".join(unit.text for unit in group if unit.text).strip()

        duration = sum(unit.duration for unit in group)

        source_blocks = list(
            dict.fromkeys(unit.block_code for unit in group if unit.block_code)
        )

        metadata = {}

        for unit in group:
            metadata.update(unit.metadata)

        metadata["source_blocks"] = source_blocks

        first = group[0]

        result.append(
            ReadingUnit(
                text=text,
                sentence_type=SentenceType.TEXT,
                metadata=metadata,
                duration=duration,
                block_type=first.block_type,
                block_code=first.block_code,
            )
        )

    def _build_pages(
        self,
        units: list[ReadingUnit],
    ) -> list[list[ReadingUnit]]:

        pages: list[list[ReadingUnit]] = []

        current: list[ReadingUnit] = []
        duration = 0.0

        for unit in units:

            if (
                unit.metadata.get("level") == 1
                and unit.sentence_type == SentenceType.TEXT
            ):

                if current:
                    pages.append(current)

                current = []
                duration = 0.0

                current.append(unit)
                duration += unit.duration

                continue

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

    def _to_book(
        self,
        book_name: str,
        pages: list[list[ReadingUnit]],
    ) -> PaginatedBook:

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

            page_datas.append(
                PageData(
                    page=page,
                    sentences=sentences,
                )
            )

        return PaginatedBook(
            book=book,
            pages=page_datas,
        )

    def _next_block(
        self,
        counter: list[int],
        block_type: str,
    ) -> tuple[str, str]:

        counter[0] += 1

        return (
            block_type,
            f"B{counter[0]:04d}",
        )

    def _spoken_unit(
        self,
        text: str,
        code: bool = False,
        block_type: str = "",
        block_code: str = "",
    ) -> ReadingUnit:

        return ReadingUnit(
            text=text,
            sentence_type=SentenceType.TEXT,
            metadata=(
                {
                    "code": True,
                }
                if code
                else {}
            ),
            duration=self._estimate_duration(text),
            block_type=block_type,
            block_code=block_code,
        )

    def _node_text(
        self,
        node: Node,
    ) -> str:

        if node.text:
            return node.text

        return " ".join(self._node_text(child) for child in node.children).strip()

    def _split_sentences(
        self,
        text: str,
    ) -> list[str]:

        return [
            part.strip() for part in self._SENTENCE_SPLIT.split(text) if part.strip()
        ]

    def _estimate_duration(
        self,
        text: str,
    ) -> float:

        words = len(text.split())

        if words == 0:
            return 0.0

        duration = words / self.WORDS_PER_SECOND

        duration += text.count(",") * 0.15
        duration += text.count(";") * 0.25
        duration += text.count(":") * 0.25
        duration += text.count(".") * 0.30
        duration += text.count("!") * 0.35
        duration += text.count("?") * 0.35

        return duration

    def _clean(
        self,
        text: str,
    ) -> str:

        return " ".join(text.split())

    def _flatten_table(
        self,
        node: Node,
    ) -> str:

        rows = []

        for row in node.children:

            cells = []

            for cell in row.children:

                cells.append(self._clean(self._node_text(cell)))

            if cells:
                rows.append(" | ".join(cells))

        return " ; ".join(rows)
