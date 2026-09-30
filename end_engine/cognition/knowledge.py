from dataclasses import replace
import re

from .deduplication import normalize
from .state import Assumption, AssumptionStatus, Claim, EvidenceStatus


class ClaimExtractor:
    """Bounded sentence extraction; confidence/evidence are never invented."""
    def extract(self, candidate):
        sentences = re.split(r"(?<=[.!?])\s+|\n+", candidate.content)
        selected = [s.strip()[:1500] for s in sentences if len(s.strip()) > 15
                    and re.search(r"\b(guarantee\w*|ensure\w*|will|always|assum\w*|enforce\w*|must)\b", s, re.I)]
        return tuple(dict.fromkeys(selected))[:8]


class KnowledgeRegister:
    def __init__(self, trajectory, extractor=None):
        self.trajectory = trajectory
        self.extractor = extractor if extractor is not None else ClaimExtractor()
        self.claims = {}
        self.assumptions = {}
        self.current_claim_ids = ()
        self._next_claim = 1
        self._next_assumption = 1

    def _record(self, kind, item, before=None):
        self.trajectory.record(kind, {"before": before, "after": item})
        self.trajectory.set("claims", tuple(self.claims.values()))
        self.trajectory.set("assumptions", tuple(self.assumptions.values()))

    def add_claim(self, text, candidate_id, *, kind="technical", status="UNVERIFIED", evidence=""):
        old = next((c for c in self.claims.values() if normalize(c.text) == normalize(text)), None)
        if old:
            return old, False
        item = Claim(f"CL{self._next_claim:03d}", text, kind, candidate_id,
                     evidence_status=EvidenceStatus(status), evidence=evidence)
        self._next_claim += 1
        self.claims[item.claim_id] = item
        self._record("claim_discovered", item)
        return item, True

    def add_assumption(self, statement, candidate_id, *, risk="HIGH", status="UNTESTED", evidence=""):
        old = next((a for a in self.assumptions.values() if normalize(a.statement) == normalize(statement)), None)
        if old:
            return old, False
        item = Assumption(f"A{self._next_assumption:03d}", statement, candidate_id, risk,
                          AssumptionStatus(status), evidence)
        self._next_assumption += 1
        self.assumptions[item.assumption_id] = item
        self._record("assumption_discovered", item)
        return item, True

    def observe_candidate(self, candidate):
        active = []
        for text in self.extractor.extract(candidate):
            claim, _ = self.add_claim(text, candidate.candidate_id)
            active.append(claim.claim_id)
            if re.search(r"\b(assum\w*|provided that|depends on)\b", text, re.I):
                self.add_assumption(text, candidate.candidate_id)
        self.current_claim_ids = tuple(active)

    def update(self, identity, status, evidence, *, assumption=False):
        register = self.assumptions if assumption else self.claims
        if identity not in register or not evidence.strip():
            raise ValueError(f"Unknown knowledge ID or missing evidence: {identity}")
        before = register[identity]
        key = "status" if assumption else "evidence_status"
        new_status = AssumptionStatus(status) if assumption else EvidenceStatus(status)
        if getattr(before, key) == new_status:
            return False
        after = replace(before, **{key: new_status, "evidence": evidence})
        register[identity] = after
        self._record("assumption_status_change" if assumption else "claim_status_change", after, before)
        return True

    def ingest(self, output, candidate_id):
        changes = 0
        for item in output.get("claims", []):
            claim, added = self.add_claim(item["text"], candidate_id, kind=item["type"],
                                         status=item["evidence_status"], evidence=item["evidence"])
            self.current_claim_ids = tuple(dict.fromkeys((*self.current_claim_ids, claim.claim_id)))
            changes += added
        for item in output.get("assumptions", []):
            _, added = self.add_assumption(item["statement"], candidate_id, risk=item["risk"],
                                          status=item["status"], evidence=item["evidence"])
            changes += added
        for field, assumption in (("claim_updates", False), ("assumption_updates", True)):
            seen = set()
            for update in output.get(field, []):
                if update["id"] in seen:
                    raise ValueError(f"Duplicate knowledge update: {update['id']}")
                seen.add(update["id"])
                changes += self.update(update["id"], update["status"], update["evidence"], assumption=assumption)
        return changes

    def compact(self):
        # Targetable IDs remain bounded in provider context; complete history lives in ledger.
        return {"claims": tuple(self.claims[c] for c in self.current_claim_ids[-8:]),
                "assumptions": tuple(self.assumptions.values())[-8:]}
