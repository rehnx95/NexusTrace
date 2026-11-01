from abc import ABC, abstractmethod

from .schemas import ExtractionResult


class Extractor(ABC):
    @abstractmethod
    def extract(self, documents: list[dict]) -> ExtractionResult:
        """Extract entities and edges from text/table documents."""
