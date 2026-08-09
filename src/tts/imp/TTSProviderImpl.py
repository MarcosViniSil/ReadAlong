from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from log.loggerService import LoggerService
from models.TTSTranscription import TTSTranscription
from tts.TTSProvider import TTSProvider

pipeline = KPipeline(lang_code='a')

SAMPLE_RATE = 24000
AUDIO_DIR = Path("audio")


class KokoroProviderImpl(TTSProvider):

    def generate(self, bookTitle: str, texts: list[str]) -> TTSTranscription:
        LoggerService.log_info(
            "Generating TTS audio for '%s' with %d phrases",
            bookTitle, len(texts)
        )

        AUDIO_DIR.mkdir(exist_ok=True)

        durations: list[float] = []
        clips: list[np.ndarray] = []

        for i, text in enumerate(texts):
            clip = self._synthesize(text)
            durations.append(self._clip_duration(clip))
            if clip is not None:
                clips.append(clip)
            LoggerService.log_info("TTS phrase %d/%d synthesized", i + 1, len(texts))

        if clips:
            final_audio = np.concatenate(clips)
            audio_path = str(AUDIO_DIR / f"{bookTitle}.wav")
            sf.write(audio_path, final_audio, SAMPLE_RATE)
            LoggerService.log_info(
                "TTS audio written to '%s' (%.2fs, %d phrases)",
                audio_path, len(final_audio) / SAMPLE_RATE, len(clips)
            )
        else:
            audio_path = ""
            LoggerService.log_warning("No audio generated for '%s' (no spoken phrases)", bookTitle)

        return TTSTranscription(audio_path=audio_path, durations=durations)

    def _synthesize(self, text: str) -> np.ndarray | None:
        generator = pipeline(text, voice='af_heart')
        chunk_audios = [audio for _, _, audio in generator]
        if not chunk_audios:
            return None
        return np.concatenate(chunk_audios)

    def _clip_duration(self, clip: np.ndarray | None) -> float:
        if clip is None:
            return 0.0
        return len(clip) / SAMPLE_RATE
