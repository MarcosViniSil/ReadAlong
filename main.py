import time

from kokoro import KPipeline
from IPython.display import display, Audio
import soundfile as sf
import torch
import numpy as np
pipeline = KPipeline(lang_code='a')
text = '''
[{'chapter_text': 'A Philosophy of Software Design John Ousterhout Stanford University', 'sentences':['A Philosophy of Software Design John Ousterhout Stanford University']}, {'chapter_text': 'A Philosophy of Software Design by John Ouster hout Copyright © 2018 John K. Ousterhout. All rights reserved. No part of this book may be reproduced, in any form or by any means, without permission in writing from the author.Published by Yaknyam Press, Palo Alto, CA. Cover design by Pete Nguyen and Shirin Oreizy (www hellonextstep.com). Printing History: April 2018: First Edition (v1.0)]]
'''
start_time = time.perf_counter()
generator = pipeline(text, voice='af_alloy')
audios = []

for i, (gs, ps, audio) in enumerate(generator):
    audios.append(audio)

final_audio = np.concatenate(audios)

sf.write('output.wav', final_audio, 24000)

end_time = time.perf_counter()
execution_time = end_time - start_time
print(f"Execution time: {execution_time:.6f} seconds")