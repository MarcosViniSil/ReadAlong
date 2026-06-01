from dataclasses import dataclass

@dataclass
class PipelineResult:
    file_path: str
    chunks: int
    audio_generated: bool