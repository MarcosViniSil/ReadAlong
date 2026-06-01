import pytest
from unittest.mock import Mock, patch
from pipeline.book_pipeline import BookPipeline
from exceptions.PipelineException import BookProcessingError
from models.PipelineResult import PipelineResult


def test_pipeline_success_returns_pipeline_result_and_calls_dependencies():
    file_path = "sample_book.txt"
    content = "This is a sample book content."
    phrases = ["This is a sample", "book content."]

    parser = Mock()
    parser.extract_text.return_value = content

    parser_factory = Mock()
    parser_factory.create.return_value = parser

    splitter = Mock()
    splitter.split_into_chunks.return_value = phrases

    tts_service = Mock()

    pipeline = BookPipeline(
        splitter=splitter,
        ttsService=tts_service,
        parser_factory=parser_factory,
    )

    with patch("pipeline.book_pipeline.LoggerService.log_info") as log_info, patch(
        "pipeline.book_pipeline.LoggerService.log_exception"
    ) as log_exception:
        result = pipeline.pipeline(file_path)

    assert isinstance(result, PipelineResult)
    assert result.file_path == file_path
    assert result.chunks == len(phrases)
    assert result.audio_generated is True

    parser_factory.create.assert_called_once_with(file_path)
    parser.extract_text.assert_called_once_with(file_path)
    splitter.split_into_chunks.assert_called_once_with(content)
    tts_service.generate.assert_called_once_with("test", phrases)

    assert log_exception.call_count == 0
    assert log_info.call_count == 3


def test_pipeline_raises_original_exception_when_text_extraction_fails():
    file_path = "broken_book.txt"
    expected_error = ValueError("cannot read file")

    parser = Mock()
    parser.extract_text.side_effect = expected_error

    parser_factory = Mock()
    parser_factory.create.return_value = parser

    splitter = Mock()
    tts_service = Mock()

    pipeline = BookPipeline(
        splitter=splitter,
        ttsService=tts_service,
        parser_factory=parser_factory,
    )

    with patch("pipeline.book_pipeline.LoggerService.log_info"), patch(
        "pipeline.book_pipeline.LoggerService.log_exception"
    ) as log_exception:
        with pytest.raises(ValueError) as exc_info:
            pipeline.pipeline(file_path)

    assert exc_info.value is expected_error
    parser_factory.create.assert_called_once_with(file_path)
    parser.extract_text.assert_called_once_with(file_path)
    splitter.split_into_chunks.assert_not_called()
    tts_service.generate.assert_not_called()
    log_exception.assert_called_once()


def test_pipeline_raises_book_processing_error_when_split_or_generate_fails():
    file_path = "sample_book.txt"
    content = "This is a sample book content."

    parser = Mock()
    parser.extract_text.return_value = content

    parser_factory = Mock()
    parser_factory.create.return_value = parser

    splitter = Mock()
    splitter.split_into_chunks.side_effect = RuntimeError("split failed")

    tts_service = Mock()

    pipeline = BookPipeline(
        splitter=splitter,
        ttsService=tts_service,
        parser_factory=parser_factory,
    )

    with patch("pipeline.book_pipeline.LoggerService.log_info"), patch(
        "pipeline.book_pipeline.LoggerService.log_exception"
    ) as log_exception:
        with pytest.raises(BookProcessingError) as exc_info:
            pipeline.pipeline(file_path)

    assert str(exc_info.value) == "An error occurred when trying to generate audio"

    parser_factory.create.assert_called_once_with(file_path)
    parser.extract_text.assert_called_once_with(file_path)
    splitter.split_into_chunks.assert_called_once_with(content)
    tts_service.generate.assert_not_called()
    log_exception.assert_called_once()


def test_pipeline_logs_success_message_after_audio_generation():
    file_path = "sample_book.txt"
    content = "One two three four."
    phrases = ["One two", "three four."]

    parser = Mock()
    parser.extract_text.return_value = content

    parser_factory = Mock()
    parser_factory.create.return_value = parser

    splitter = Mock()
    splitter.split_into_chunks.return_value = phrases

    tts_service = Mock()

    pipeline = BookPipeline(
        splitter=splitter,
        ttsService=tts_service,
        parser_factory=parser_factory,
    )

    with patch("pipeline.book_pipeline.LoggerService.log_info") as log_info, patch(
        "pipeline.book_pipeline.LoggerService.log_exception"
    ):
        pipeline.pipeline(file_path)

    assert log_info.call_count == 3
    assert "received file_path" in log_info.call_args_list[0].args[0]
    assert "content from file path" in log_info.call_args_list[1].args[0]
    assert "audio generated successfully" in log_info.call_args_list[2].args[0]


def test_pipeline_raises_original_exception_when_parser_factory_creation_fails():
    file_path = "unsupported.xyz"
    expected_error = ValueError("unsupported format")

    parser_factory = Mock()
    parser_factory.create.side_effect = expected_error

    splitter = Mock()
    tts_service = Mock()

    pipeline = BookPipeline(
        splitter=splitter,
        ttsService=tts_service,
        parser_factory=parser_factory,
    )

    with patch("pipeline.book_pipeline.LoggerService.log_info"), patch(
        "pipeline.book_pipeline.LoggerService.log_exception"
    ) as log_exception:
        with pytest.raises(ValueError) as exc_info:
            pipeline.pipeline(file_path)

    assert exc_info.value is expected_error
    parser_factory.create.assert_called_once_with(file_path)
    splitter.split_into_chunks.assert_not_called()
    tts_service.generate.assert_not_called()
    log_exception.assert_called_once()


def test_pipeline_raises_book_processing_error_when_tts_generate_fails():
    file_path = "sample_book.txt"
    content = "This is a sample book content."
    phrases = ["This is a sample", "book content."]

    parser = Mock()
    parser.extract_text.return_value = content

    parser_factory = Mock()
    parser_factory.create.return_value = parser

    splitter = Mock()
    splitter.split_into_chunks.return_value = phrases

    tts_service = Mock()
    tts_service.generate.side_effect = RuntimeError("tts failed")

    pipeline = BookPipeline(
        splitter=splitter,
        ttsService=tts_service,
        parser_factory=parser_factory,
    )

    with patch("pipeline.book_pipeline.LoggerService.log_info"), patch(
        "pipeline.book_pipeline.LoggerService.log_exception"
    ) as log_exception:
        with pytest.raises(BookProcessingError) as exc_info:
            pipeline.pipeline(file_path)

    assert str(exc_info.value) == "An error occurred when trying to generate audio"

    parser_factory.create.assert_called_once_with(file_path)
    parser.extract_text.assert_called_once_with(file_path)
    splitter.split_into_chunks.assert_called_once_with(content)
    tts_service.generate.assert_called_once_with("test", phrases)
    log_exception.assert_called_once()


def test_pipeline_with_empty_content():
    file_path = "empty_book.txt"
    content = ""
    phrases = []

    parser = Mock()
    parser.extract_text.return_value = content

    parser_factory = Mock()
    parser_factory.create.return_value = parser

    splitter = Mock()
    splitter.split_into_chunks.return_value = phrases

    tts_service = Mock()

    pipeline = BookPipeline(
        splitter=splitter,
        ttsService=tts_service,
        parser_factory=parser_factory,
    )

    with patch("pipeline.book_pipeline.LoggerService.log_info"), patch(
        "pipeline.book_pipeline.LoggerService.log_exception"
    ):
        result = pipeline.pipeline(file_path)

    assert isinstance(result, PipelineResult)
    assert result.file_path == file_path
    assert result.chunks == 0
    assert result.audio_generated is True

    parser.extract_text.assert_called_once_with(file_path)
    splitter.split_into_chunks.assert_called_once_with(content)
    tts_service.generate.assert_called_once_with("test", phrases)
