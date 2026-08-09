from abc import ABC, abstractmethod

from models.Node import Node

class BookParser(ABC):

    @abstractmethod
    def extract_text(self, file_path: str) -> Node:
        pass