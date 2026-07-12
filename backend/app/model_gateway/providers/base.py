from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderResponse:
    content: str
    input_tokens: int
    output_tokens: int


class ModelProvider(ABC):
    @abstractmethod
    async def complete(
        self, *, model: str, messages: list[dict[str, str]], max_tokens: int
    ) -> ProviderResponse: ...
