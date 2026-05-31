# EPUB to Audio Converter with Kokoro TTS

A Python-based system for converting EPUB files to audio using the Kokoro text-to-speech model with precise sentence-level timing and page navigation.

## Features

- **EPUB Processing**: Extract and clean text from EPUB files
- **Sentence Segmentation**: Intelligent sentence splitting with timing information
- **Kokoro TTS Integration**: High-quality voice synthesis
- **Page-based Navigation**: Structured audio output with page navigation
- **Timing Metadata**: Precise sentence timing within audio files
- **REST API**: Web interface for file upload and processing

## Architecture

```
src/
├── core/           # Core business logic
├── services/       # External service integrations
├── api/           # Web API endpoints
├── models/        # Data models and schemas
├── utils/         # Utility functions
└── main.py        # Application entry point
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python src/main.py
```

3. Upload an EPUB file via the web interface at `http://localhost:8000`

## Usage

### Basic Conversion
```python
from src.core.converter import EPUBAudioConverter

converter = EPUBAudioConverter()
result = converter.convert("book.epub", voice="af_heart")
```

### API Endpoints
- `POST /upload`: Upload EPUB file
- `GET /status/{job_id}`: Check conversion status
- `GET /download/{page_id}`: Download audio page
- `GET /metadata/{book_id}`: Get book metadata

## Output Format

Each page is represented as:
```json
{
  "page_id": 1,
  "audio_file": "page_1.mp3",
  "sentences": [
    {
      "id": 1,
      "text": "This is a sentence.",
      "start": 0.0,
      "end": 2.5
    }
  ],
  "next_page": 2,
  "prev_page": null
}
```

## Configuration

See `config/settings.yaml` for:
- Audio quality settings
- Voice selection
- Processing parameters
- Storage paths

## License

MIT License