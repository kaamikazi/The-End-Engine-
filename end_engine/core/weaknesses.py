from dataclasses import replace
from ..cognition.deduplication import TokenFindingDeduplicator

from ..models.protocol import INVALID_REFERENCE, ModelProtocolError
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
                raise ModelProtocolError(INVALID_REFERENCE, f"Critique references unknown weakness {identity}",
                                         invalid=(identity,), allowed={"weakness_ids": sorted(self._items)})
            if identity is None:
                identity = self.deduplicator.match(finding, self.snapshot(), target_id)
            old = self._items.get(identity)
            authority = finding.get('_assessment', {})
            if old and old.authority_status == 'VALIDATED_WITHIN_SCOPE' and authority and not authority['decisive']:
                found.append(old)  # A lower-trust rediscovery cannot erase or reopen a validated concern.
                continue
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
            if authority:
                item = replace(item, source_origin=authority['source_origin'],
                               authority_status=authority['authority_status'], decisive=authority['decisive'])
            self._items[item.id] = item
            found.append(item)
        return tuple(found)

    def deciding(self):
        return tuple(w for w in self.snapshot() if w.decisive)

    def partition_updates(self, updates):
        """(valid, rejected) where rejected holds (update, reason). Each update is judged independently."""
        valid, rejected, seen = [], [], set()
        for update in updates:
            reason = ("unknown weakness ID" if update.id not in self._items else "duplicate update" if update.id in seen
                      else "missing reason" if not update.reason.strip() else
                      "invalid status" if not isinstance(update.status, WeaknessStatus) else None)
            seen.add(update.id)
            if reason:
                rejected.append((update, reason))
            else:
                valid.append(update)
        return tuple(valid), tuple(rejected)

    def apply_updates(self, updates):
        seen = set()
        for update in updates:
            if update.id not in self._items or update.id in seen or not update.reason.strip():
                raise ModelProtocolError(INVALID_REFERENCE, f"Invalid or duplicate weakness update: {update.id}",
                                         invalid=(update.id,), allowed={"weakness_ids": sorted(self._items)})
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
