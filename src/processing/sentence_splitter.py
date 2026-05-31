
class Splitter():
    
    def split_into_chunks(self,text: str, chunk_size: int = 5) -> list[str]:
        words = text.split()

        return [
            " ".join(words[i:i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]