import re
from typing import Protocol


def normalize(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


class FindingDeduplicator(Protocol):
    def match(self, finding: dict, existing: tuple, target_id: str | None = None) -> str | None: ...


class TokenFindingDeduplicator:
    """Conservative category/target-aware lexical similarity; no semantic model."""
    def __init__(self, threshold=0.72):
        if not 0 < threshold <= 1:
            raise ValueError("threshold must be in (0,1]")
        self.threshold = threshold

    def match(self, finding, existing, target_id=None):
        text = normalize(finding["description"])
        tokens = set(text.split()) - {"a", "an", "the", "is", "are", "of", "to", "and"}
        for item in existing:
            if item.type != finding["type"]:
                continue
            if item.target_id and target_id and item.target_id != target_id:
                continue
            other = normalize(item.description)
            words = set(other.split()) - {"a", "an", "the", "is", "are", "of", "to", "and"}
            similarity = len(tokens & words) / max(1, len(tokens | words))
            # Opposite polarity should not be conflated even with heavy token overlap.
            negative = {"not", "never", "no", "without"}
            same_polarity = bool(tokens & negative) == bool(words & negative)
            if text == other or (same_polarity and len(tokens & words) >= 3 and similarity >= self.threshold):
                return item.id
        return None
