from enum import Enum

class JobType(Enum):
    ANALYZE_GRAMMAR = "analyze_grammar"
    GENERATE_AUDIO = "generate_audio"
    GENERATE_HLS = "generate_hls"

    def __str__(self) -> str:  
	    return self.value