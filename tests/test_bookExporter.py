import json
from pathlib import Path

from export.bookExporter import serialize_book, write_book_json
from models.Node import Node
from models.SentenceType import SentenceType
from models.TTSTranscription import TTSTranscription
from models.enum.NodeType import NodeType
from pipeline.book_pipeline import BookPipeline
from processing.paginator import Paginator


class FakeDetection:
    def detect_extension(self, file_path):
        return ".txt"


class FakeParser:
    def __init__(self, root: Node):
        self.root = root

    def extract_text(self, file_path):
        return self.root


class FakeParserFactory:
    def __init__(self, root: Node):
        self.root = root

    def create(self, extension):
        return FakeParser(self.root)


class FakeTTS:
    def __init__(self, durations):
        self.durations = durations

    def generate(self, bookTitle, texts):
        return TTSTranscription(
            audio_path=f"audio/{bookTitle}.wav",
            durations=self.durations,
        )


def build_document(*children) -> Node:
    return Node(type=NodeType.DOCUMENT, children=list(children))


def paragraph(*sentences: str) -> Node:
    return Node(
        type=NodeType.PARAGRAPH,
        children=[Node(type=NodeType.TEXT, text=s) for s in sentences],
    )


def test_serialize_book_shape_and_timings():
    root = build_document(
        paragraph("First sentence. Second sentence."),
        Node(type=NodeType.IMAGE, metadata={"src": "cover.jpg"}),
        paragraph("Third."),
    )
    book = Paginator().paginate(root, "My Book")

    data = serialize_book(book)

    assert data["bookName"] == "My Book"
    assert data["bookCode"] == "my-book"
    assert data["audioFile"] == ""
    assert len(data["pages"]) == 1

    page = data["pages"][0]
    assert page["pageCode"] == "P001"
    assert page["nextPageCode"] == ""
    assert page["start"] == 0.0

    sentences = page["sentences"]
    assert [s["sentenceType"] for s in sentences] == [
        SentenceType.TEXT.value,
        SentenceType.TEXT.value,
        SentenceType.IMAGE.value,
        SentenceType.TEXT.value,
    ]

    # Estimated durations from the paginator (words / 2.5 wps).
    assert sentences[0]["text"] == "First sentence."
    assert sentences[0]["duration"] == 0.8
    assert sentences[0]["start"] == 0.0
    assert sentences[0]["end"] == 0.8

    # Non-spoken marker consumes no time.
    assert sentences[2]["sentenceType"] == SentenceType.IMAGE.value
    assert sentences[2]["duration"] == 0.0
    assert sentences[2]["start"] == sentences[2]["end"]

    assert sentences[3]["start"] == sentences[2]["end"]
    assert data["duration"] == sentences[-1]["end"]
    assert page["end"] == sentences[-1]["end"]


def test_write_book_json_uses_book_code(tmp_path):
    root = build_document(paragraph("Hello world."))
    book = Paginator().paginate(root, "O Segredo do Vale")

    path = write_book_json(book, tmp_path)

    assert path == tmp_path / "o-segredo-do-vale.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["bookCode"] == "o-segredo-do-vale"
    assert data["pages"][0]["sentences"][0]["text"] == "Hello world."


def test_pipeline_writes_json_with_real_timings_and_audio(tmp_path):
    root = build_document(
        paragraph("First sentence. Second sentence."),
        Node(type=NodeType.IMAGE, metadata={"src": "cover.jpg"}),
        paragraph("Third."),
    )
    tts = FakeTTS(durations=[2.0, 3.0, 1.5])
    pipeline = BookPipeline(
        splitter=None,
        ttsService=tts,
        parser_factory=FakeParserFactory(root),
        filetypeDetection=FakeDetection(),
        paginator=Paginator(),
        output_dir=tmp_path,
    )
    file_path = tmp_path / "My Book.txt"
    file_path.write_text("irrelevant", encoding="utf-8")

    result = pipeline.pipeline(file_path)

    assert result.json_path == str(tmp_path / "my-book.json")
    assert result.audio_generated is True

    data = json.loads(Path(result.json_path).read_text(encoding="utf-8"))
    assert data["audioFile"] == "audio/My Book.wav"
    assert data["duration"] == 6.5

    sentences = data["pages"][0]["sentences"]
    assert sentences[0]["start"] == 0.0
    assert sentences[0]["end"] == 2.0
    assert sentences[1]["start"] == 2.0
    assert sentences[2]["sentenceType"] == SentenceType.IMAGE.value
    assert sentences[3]["end"] == 6.5
