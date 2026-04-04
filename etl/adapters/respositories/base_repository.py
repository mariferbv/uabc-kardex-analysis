from abc import ABC, abstractmethod
from typing import Dict, Any

class IKardexRepository(ABC):
    @abstractmethod
    def save(self, student_data: Dict[str, Any]) -> bool:
        """Receives a student data dictionary and persists it in the desired storage (DB, file, etc.)
        Returns True if the operation was successful, False otherwise."""
        pass