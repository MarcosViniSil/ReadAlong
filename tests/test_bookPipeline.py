from pathlib import Path

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
        self.last_title = None
        self.last_texts = None

    def generate(self, bookTitle, texts):
        self.last_title = bookTitle
        self.last_texts = texts
        return TTSTranscription(
            audio_path=f"audio/{bookTitle}.wav",
            durations=self.durations,
        )


def build_document(*children) -> Node:
    return Node(type=NodeType.DOCUMENT, children=list(children))


def paragraph(*sentences: str) -> Node:
    return Node(type=NodeType.PARAGRAPH, children=[Node(type=NodeType.TEXT, text=s) for s in sentences])


def make_pipeline(root: Node, tts: FakeTTS) -> BookPipeline:
    return BookPipeline(
        splitter=None,
        ttsService=tts,
        parser_factory=FakeParserFactory(root),
        filetypeDetection=FakeDetection(),
        paginator=Paginator(),
    )



def test_pipeline_without_spoken_sentences_generates_no_audio(tmp_path):
    root = build_document(Node(type=NodeType.IMAGE, metadata={"src": "cover.jpg"}))
    tts = FakeTTS(durations=[])
    pipeline = make_pipeline(root, tts)
    file_path = tmp_path / "Silent Book.txt"
    file_path.write_text("irrelevant", encoding="utf-8")

    result = pipeline.pipeline(file_path)

    assert result.chunks == 1
    assert result.audio_generated is False
    assert tts.last_texts is None


def test_generate_audio_fills_real_timings_and_audio_file():
    root = build_document(
        paragraph("First sentence. Second sentence."),
        Node(type=NodeType.IMAGE, metadata={"src": "cover.jpg"}),
        paragraph("Third."),
    )
    tts = FakeTTS(durations=[2.0, 3.0, 1.5])
    pipeline = make_pipeline(root, tts)
    paginated = Paginator().paginate(root, "My Book")

    pipeline._BookPipeline__generate_audio(paginated)

    assert tts.last_texts == ["First sentence.", "Second sentence.", "Third."]

    sentences = paginated.pages[0].sentences

    # First sentence: real duration 2.0s, starts the global timeline.
    assert sentences[0].text == "First sentence."
    assert sentences[0].duration == 2.0
    assert sentences[0].start == 0.0
    assert sentences[0].end == 2.0

    # Second sentence: 3.0s, follows on the timeline.
    assert sentences[1].duration == 3.0
    assert sentences[1].start == 2.0
    assert sentences[1].end == 5.0

    # Non-spoken marker keeps its position but consumes no time.
    assert sentences[2].sentenceType == SentenceType.IMAGE
    assert sentences[2].duration == 0.0
    assert sentences[2].start == 5.0
    assert sentences[2].end == 5.0

    # Third sentence: 1.5s after the marker.
    assert sentences[3].duration == 1.5
    assert sentences[3].start == 5.0
    assert sentences[3].end == 6.5

    # Book points to the single concatenated audio file.
    assert paginated.audio_file == "audio/My Book.wav"
