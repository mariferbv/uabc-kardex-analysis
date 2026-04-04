from abc import ABC, abstractmethod
from typing import Any, Optional

class IKardexParser(ABC):
    @abstractmethod
    def reset(self):
        """Reset any parser state, useful for a new document or process"""
        pass

    @abstractmethod
    def parse_line(self, line: str) -> Optional[dict]:
        """Analyze a single line of text and update internal state.
        May returns a dictionary if a record is complete"""
        pass

    @abstractmethod
    def get_results(self) -> Any:
        """Returns a final processed object (Student with all its courses, etc.)"""
        pass