from abc import ABC, abstractmethod

from ..models.base import ModelProvider, ModelRequest, ModelResponse
from ..models.recording import RecordingProvider


class JudgeProvider(ABC):
    """Separate evaluation transport. No candidate-writing API is exposed."""
    @abstractmethod
    def evaluate(self, request: ModelRequest) -> ModelResponse: ...

    @abstractmethod
    def metadata(self) -> dict: ...

    def for_run(self):
        """Stateless adapters may share transport. Stateful fixtures override this."""
        return self


class ModelJudgeProvider(JudgeProvider):
    def __init__(self, provider: ModelProvider):
        self.provider = provider

    def evaluate(self, request):
        return self.provider.generate_structured(request)

    def metadata(self):
        return self.provider.metadata()


class _JudgeBridge(ModelProvider):
    def __init__(self, judge, role):
        self.judge, self.role = judge, role

    def metadata(self):
        return {**self.judge.metadata(), "role": self.role}

    def generate_structured(self, request):
        return self.judge.evaluate(request)

    def generate(self, request):
        raise ValueError("Judges return structured artifacts only")


def recorded_judge(judge, trajectory, role, repair_attempts=0):
    return RecordingProvider(_JudgeBridge(judge.for_run(), role), trajectory, repair_attempts)
