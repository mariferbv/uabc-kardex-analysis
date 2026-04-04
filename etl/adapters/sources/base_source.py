from abc import ABC, abstractmethod
from typing import Any

class IKardexSource(ABC):
    @abstractmethod
    def fetch_data(self, path: str) -> Any:
        """Recieves a path or identifier and returns raw data to be parsed"""
        pass