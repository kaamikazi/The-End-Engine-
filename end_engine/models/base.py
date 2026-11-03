from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelRequest:
    purpose: str
    prompt: str
    context: dict[str, Any]
    schema: dict | None = None


@dataclass(frozen=True)
class ModelResponse:
    content: Any
    usage: dict[str, int] | None = None
    tool_calls: tuple[dict, ...] = ()
    # Optional adapter-owned final output boundary, never inferred from a model's JSON authority fields.
    answer_content: str | None = None


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Return ordinary text; credentials belong in the adapter, never metadata."""

    @abstractmethod
    def generate_structured(self, request: ModelRequest) -> ModelResponse:
        """Return JSON-compatible data matching request.schema."""

    @abstractmethod
    def metadata(self) -> dict:
        """Return JSON-safe provider/model/version identifiers without secrets."""
