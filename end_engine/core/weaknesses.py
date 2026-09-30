from dataclasses import replace
from ..cognition.deduplication import TokenFindingDeduplicator

from .state import Weakness, WeaknessStatus


class WeaknessRegistry:
    def __init__(self, deduplicator=None):
        self._items = {}
        self._next_id = 1
        self.deduplicator = deduplicator if deduplicator is not None else TokenFindingDeduplicator()

    def snapshot(self):
        return tuple(self._items.values())

    def open(self):
        return tuple(w for w in self._items.values() if w.status is WeaknessStatus.OPEN)

    def restore(self, snapshot):
        self._items = {w.id: w for w in snapshot}

    def ingest(self, findings, iteration, target_id=None):
        found = []
        for finding in findings:
            identity = finding["weakness_id"]
            if identity is not None and identity not in self._items:
                raise ValueError(f"Critique references unknown weakness {identity}")
            if identity is None:
                identity = self.deduplicator.match(finding, self.snapshot(), target_id)
            old = self._items.get(identity)
            if old:
                # A rediscovered issue reopens; old candidate/critique snapshots remain intact.
                item = replace(old, type=finding["type"], severity=finding["severity"],
                               description=finding["description"], evidence=finding["evidence"],
                               status=WeaknessStatus.OPEN, last_seen_iteration=iteration,
                               occurrences=old.occurrences + 1, status_reason="Rediscovered by critique")
            else:
                item = Weakness(f"W{self._next_id:03d}", finding["type"], finding["severity"],
                                finding["description"], finding["evidence"],
                                first_seen_iteration=iteration, last_seen_iteration=iteration, target_id=target_id)
                self._next_id += 1
            self._items[item.id] = item
            found.append(item)
        return tuple(found)

    def apply_updates(self, updates):
        seen = set()
        for update in updates:
            if update.id not in self._items or update.id in seen or not update.reason.strip():
                raise ValueError(f"Invalid or duplicate weakness update: {update.id}")
            if not isinstance(update.status, WeaknessStatus):
                raise ValueError(f"Invalid weakness status for {update.id}")
            seen.add(update.id)
        changes = []
        for update in updates:
            before = self._items[update.id]
            after = replace(before, status=update.status, status_reason=update.reason)
            self._items[update.id] = after
            changes.append({"before": before, "after": after})
        return changes
