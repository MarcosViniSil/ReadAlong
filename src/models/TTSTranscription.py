from dataclasses import dataclass


@dataclass
class TTSTranscription:
    audio_path: str
    durations: list[float]
