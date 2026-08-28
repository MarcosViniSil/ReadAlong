from pathlib import Path

from models.Node import Node
from models.enum.NodeType import NodeType
from pipeline.book_pipeline import BookPipeline
from processing.chunker import Chunker
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


class FakeAudioQueue:
    """In-memory queue: records published jobs, returns canned responses."""

    def __init__(self, response_builder=None):
        self.published = []
        self.response_builder = response_builder or _simple_response_builder

    def publish_jobs(self, messages):
        self.published.extend(messages)

    def wait_for_results(self, expected_chunk_ids, timeout=300.0):
        by_chunk = {m["chunk_id"]: m for m in self.published}
        return {
            chunk_id: self.response_builder(by_chunk[chunk_id])
            for chunk_id in expected_chunk_ids
        }


def _simple_response_builder(message: dict) -> dict:
    """Reply to a job with fake word timings for each sentence."""
    sentences = []
    cursor = 0.0
    for sentence in message["sentences"]:
        words = [
            {"text": "word", "start": cursor, "end": cursor + 1.0},
        ]
        sentences.append({
            "segmentCode": sentence["segmentCode"],
            "start": cursor,
            "end": cursor + 1.0,
            "duration": 1.0,
            "words": words,
        })
        cursor += 1.0
    return {
        "chunk_id": message["chunk_id"],
        "audio_url": f"audio/chunks/{message['chunk_id']}.wav",
        "sentences": sentences,
    }


def build_document(*children) -> Node:
    return Node(type=NodeType.DOCUMENT, children=list(children))


def paragraph(*sentences: str) -> Node:
    return Node(type=NodeType.PARAGRAPH, children=[Node(type=NodeType.TEXT, text=s) for s in sentences])


def make_pipeline(root: Node, queue: FakeAudioQueue, tmp_path) -> BookPipeline:
    return BookPipeline(
        splitter=None,
        chunker=Chunker(),
        parser_factory=FakeParserFactory(root),
        filetypeDetection=FakeDetection(),
        paginator=Paginator(),
        audio_queue=queue,
        output_dir=tmp_path,
    )


def test_pipeline_without_spoken_sentences_publishes_no_jobs(tmp_path):
    root = build_document(Node(type=NodeType.IMAGE, metadata={"src": "cover.jpg"}))
    queue = FakeAudioQueue()
    pipeline = make_pipeline(root, queue, tmp_path)
    file_path = tmp_path / "Silent Book.txt"
    file_path.write_text("irrelevant", encoding="utf-8")

    result = pipeline.pipeline(file_path)

    assert queue.published == []
    assert result.chunks == 0
    assert result.audio_generated is False


def test_pipeline_publishes_one_job_per_chunk_and_merges_timings(tmp_path):
    root = build_document(paragraph("First sentence. Second sentence."))
    queue = FakeAudioQueue()
    pipeline = make_pipeline(root, queue, tmp_path)
    file_path = tmp_path / "My Book.txt"
    file_path.write_text("irrelevant", encoding="utf-8")

    result = pipeline.pipeline(file_path)

    assert result.audio_generated is True
    assert len(queue.published) >= 1

    message = queue.published[0]
    assert message["type"] == "generate_audio"
    assert message["chunk_id"]
    assert message["page_code"] == "P001"
    assert message["book_title"] == "My Book"
    assert message["content"]
    assert message["sentences"] == [
        {"segmentCode": "S0001", "text": "First sentence."},
        {"segmentCode": "S0002", "text": "Second sentence."},
    ]

    # Merged timings landed on the spoken sentences' audio blocks.
    page_json = (tmp_path / "my-book" / "pages" / "P001.json").read_text(encoding="utf-8")
    assert '"chunk_id"' in page_json
    assert '"words"' in page_json
