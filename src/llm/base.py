from abc import ABC, abstractmethod


class LLM(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str = "", temperature: float = 0.0) -> str:
        ...
