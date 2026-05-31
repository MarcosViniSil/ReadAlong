from tts.TTSProvider import TTSProvider
from kokoro import KPipeline
import soundfile as sf
import numpy as np

pipeline = KPipeline(lang_code='a')

class KokoroProviderImpl(TTSProvider):
    
    def generate(self, bookTitle:str,texts: list[str]) -> str:
        for i,text in enumerate(texts):
            print(text)
            generator = pipeline(text, voice='af_heart')
            audios = []

            for j, (_, _, audio) in enumerate(generator):
                audios.append(audio)

            final_audio = np.concatenate(audios)

            sf.write(f'./audio/{bookTitle}-{i}.wav', final_audio, 24000)
        