from pathlib import Path
import os
import tempfile
from typing import Protocol
from uuid import UUID

from .serializer import dumps, loads


class Ledger(Protocol):
    def save(self, trajectory: dict) -> str: ...
    def load(self, path: str) -> dict: ...


class JsonLedger:
    """One complete JSONL record per file, committed via atomic replacement."""

    def __init__(self, directory="trajectories"):
        self.directory = Path(directory)

    def save(self, trajectory):
        name = str(UUID(trajectory["trajectory_id"]))
        text = dumps(trajectory) + "\n"
        self.directory.mkdir(parents=True, exist_ok=True)
        destination = self.directory / f"{name}.jsonl"
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                             dir=self.directory, suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        return str(destination.resolve())

    def load(self, path):
        return loads(Path(path).read_text(encoding="utf-8"))
