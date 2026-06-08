from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, task: str, **kwargs) -> Any:
        """Execute the agent's main task."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
