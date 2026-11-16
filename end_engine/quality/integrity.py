"""Evidence integrity (v0.3.3, corrected in v0.3.4): a model statement is a claim, never verification.

Deterministic and offline. No model is called, no reference is repaired or substituted, and nothing is dropped.
* Every evidence reference a model makes in a bounded explicit form is resolved against evidence recorded in this run.
* A trusted checker PASS supports only the claims it targets, and only within its declared scope: this candidate, the
  exact checked artifact, the statements it declares, and its phase (claims matching the final-scope phrase list need a
  "final" phase). A PASS that targets nothing recorded supports nothing.
* Claim-status provenance comes from the updates the Engine wrote, never from evidence wording.
* Model agreement is corroboration. Accepted risks and explanations stay unverified.
* Contradictions stay visible; no side is chosen by recency or confidence.
Findings become gate uncertainties. They cap acceptance at provisional; they never invent a failure.
This is not a fact checker: unreferenced statements in candidates, critiques or weaknesses are not examined."""
import hashlib
import re
from dataclasses import dataclass, field

from ..cognition.deduplication import normalize
from ..core.output_format import consensus_kind
from ..core.state import to_data

STATES = ("model_claimed", "evidence_referenced", "evidence_validated", "checker_supported", "verified",
          "unresolved", "unsupported")
# Wording of the knowledge text the Engine writes. A model can write the same words, so provenance is established by
# the (claim, status, evidence) updates the session actually made, never by this prefix.
ENGINE_EVIDENCE_PREFIX = "Executed evidence references: "

# Statements about final-task success or complete correctness. Only a check declaring phase "final" can support
# them; development-scope or undeclared-phase evidence cannot. Deliberately narrow: this is not a fact checker.
FINAL_SCOPE = re.compile(
    r"\b(final[- ](evaluation|task|test|check|grading|score)s?|hidden[- ]tests?|held[- ]out|"
    r"reference[- ](evaluation|check|solution|tests?)|production[- ](ready|verified)|"
    r"all\s+(the\s+)?(tests|checks|constraints|requirements)\s+(pass|passed|hold|are\s+(met|satisfied))|"
    r"fully\s+(correct|verified|satisf\w*)|complete\s+(correctness|verification))\b", re.I)

# Bounded, explicit reference forms. Ordinary prose is never treated as a reference.
_SOURCE = re.compile(r"(?:harness:[\w.-]+:)?receipts/[\w.-]+\.json")
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
_HASH = re.compile(r"\b(?=[0-9a-f]*[0-9])(?=[0-9a-f]*[a-f])[0-9a-f]{12,64}\b", re.I)
_RECORD = re.compile(r"\b(E-C\d+-\d+|AT\d{3,}|AJ\d{3,}|J\d{3,}|CL\d{3,}|W\d{3,}|A\d{3,})\b")
_STEP = re.compile(r"\bstep\s+#?(\d+)\b", re.I)


def content_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_final_scope(text):
    return bool(FINAL_SCOPE.search(text or ""))


def _get(item, key, default=None):
    return item.get(key, default) if isinstance(item, dict) else getattr(item, key, default)


def artifact_mismatch(artifact, digest):
    """True when the checker declares a checked artifact that is not this exact content (or cannot be compared)."""
    declared = _get(_get(artifact, "contract") or {}, "artifact_sha256")
    return bool(declared) and (digest is None or declared.lower() != digest)


def scope_gap(artifact, claim, digest):
    """Why a passed executed check targeting this claim does not support it, or None when it is in scope."""
    contract = _get(artifact, "contract")
    if artifact_mismatch(artifact, digest):
        return "checked a different artifact"
    declared = _get(contract, "claims") or ()
    if declared and normalize(claim.text) not in {normalize(c) for c in declared}:
        return "claim is outside the statements the check declares"
    if is_final_scope(claim.text) and _get(contract, "phase") != "final":
        return ("development-scope evidence cannot support a final-task claim" if contract else
                "evidence with undeclared phase cannot support a final-task claim")
    return None


def references_in(text):
    found, rest = [], text or ""
    for kind, pattern in (("source", _SOURCE), ("execution_id", _UUID), ("hash", _HASH)):
        found += [(kind, m.group(0)) for m in pattern.finditer(rest)]
        rest = pattern.sub(" ", rest)
    found += [("record", m.group(1)) for m in _RECORD.finditer(rest)]
    found += [("step", m.group(1)) for m in _STEP.finditer(rest)]
    return tuple(dict.fromkeys(found))


@dataclass(frozen=True)
class EvidenceReference:
    source: str               # where the model made the reference, e.g. "AJ001.uncertainties[0]"
    reference: str            # exactly as written by the model
    kind: str                 # artifact | execution_id | source | hash | record | step
    status: str               # valid | nonexistent | wrong_candidate | wrong_artifact
    resolved_to: str | None = None
    owner: str | None = None  # candidate the resolved record belongs to, when candidate-bound


@dataclass(frozen=True)
class ClaimIntegrity:
    claim_id: str
    text: str
    model_status: str         # status held in the knowledge register when evaluated
    status_source: str        # model | engine | none
    status: str               # one of STATES
    history: tuple[str, ...]
    reason: str
    supporting: tuple[str, ...] = ()
    out_of_scope: tuple[tuple[str, str], ...] = ()
    contradicting: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    consensus: str = ""       # v0.3.5: MODEL_CONSENSUS / REPORTED_CONSENSUS when the model's support is agreement


@dataclass(frozen=True)
class StatementIntegrity:
    source: str
    text: str                 # original model text, unmodified
    status: str
    history: tuple[str, ...]
    reason: str
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class Contradiction:
    target: str
    supporting: tuple[str, ...]
    opposing: tuple[str, ...]
    resolution: str = "unresolved; no side is selected by recency or confidence"


@dataclass(frozen=True)
class IntegrityReport:
    candidate_id: str
    content_sha256: str
    claims: tuple[ClaimIntegrity, ...]
    statements: tuple[StatementIntegrity, ...]
    references: tuple[EvidenceReference, ...]
    contradictions: tuple[Contradiction, ...]
    trusted_evidence: tuple[dict, ...]
    model_agreement: dict
    accepted_risks: tuple[dict, ...]
    uncertainties: tuple[str, ...] = ()
    status_counts: dict = field(default_factory=dict)


class EvidenceIndex:
    """Everything a model reference may legitimately point to: evidence and records actually recorded in this run."""
    def __init__(self, record, candidate, *, evidence=(), judgments=(), claims=(), weaknesses=(), assumptions=()):
        self.candidate_id = candidate.candidate_id
        self.digest = content_sha256(candidate.content)
        self.artifacts = {_get(a, "artifact_id"): to_data(a) for a in (*record.get("verifier_evidence", ()), *evidence)}
        self.hashes = {c["candidate_id"]: content_sha256(c.get('answer_content') if c.get('answer_content') is not None
                       else c['content']) for c in record.get("candidates", ())}
        self.hashes[candidate.candidate_id] = self.digest
        self.tests = {t["test_id"]: t["candidate_id"] for t in record.get("adversarial_tests", ())}
        self.judgments = {j["judgment_id"]: j["candidate_id"]
                          for j in (*record.get("judgments", ()), *record.get("adversarial_judgments", ()))}
        self.judgments.update({j.judgment_id: j.candidate_id for j in judgments})
        self.unbound = {*(_get(c, "claim_id") for c in (*record.get("claims", ()), *claims)),
                        *(_get(w, "id", w) for w in (*record.get("weaknesses", ()), *weaknesses)),
                        *(_get(a, "assumption_id", a) for a in (*record.get("assumptions", ()), *assumptions))}
        self.steps = len(record.get("steps", ()))
        runs = {m.group(1).lower() for a in self.artifacts.values()
                for m in [re.match(r"harness:([\w-]+):", a.get("source") or "")] if m}
        self.runs = runs | {str(record.get("trajectory_id", "")).lower()} - {""}

    def _bound(self, source, reference, kind, resolved, owner, artifact=None):
        status = ("wrong_candidate" if owner not in (None, self.candidate_id) else
                  "wrong_artifact" if artifact is not None and artifact_mismatch(artifact, self.digest) else "valid")
        return EvidenceReference(source, reference, kind, status, resolved, owner)

    def resolve(self, source, kind, reference):
        missing = EvidenceReference(source, reference, kind, "nonexistent")
        if kind in ("artifact", "execution_id") or (kind == "record" and reference.startswith("E-")):
            artifact = self.artifacts.get(reference)
            if artifact is None and kind == "execution_id":
                artifact = next((a for a in self.artifacts.values() if reference.lower() in (a.get("source") or "").lower()), None)
                if artifact is None and reference.lower() in self.runs:
                    return EvidenceReference(source, reference, kind, "valid", "run record")
            return self._bound(source, reference, kind, artifact["artifact_id"], artifact["candidate_id"], artifact) \
                if artifact else missing
        if kind == "source":
            artifact = next((a for a in self.artifacts.values() if (a.get("source") or "").endswith(reference)), None)
            return self._bound(source, reference, kind, artifact["artifact_id"], artifact["candidate_id"], artifact) \
                if artifact else missing
        if kind == "hash":
            low = reference.lower()
            if self.digest.startswith(low):
                return EvidenceReference(source, reference, kind, "valid", "content of " + self.candidate_id, self.candidate_id)
            owner = next((c for c, h in self.hashes.items() if h.startswith(low)), None)
            if owner:
                return self._bound(source, reference, kind, "content of " + owner, owner)
            artifact = next((a for a in self.artifacts.values()
                             if (_get(a.get("contract") or {}, "artifact_sha256") or "").lower().startswith(low)), None)
            return self._bound(source, reference, kind, artifact["artifact_id"], artifact["candidate_id"], artifact) \
                if artifact else missing
        if kind == "step":
            return EvidenceReference(source, reference, kind, "valid", f"step {reference}") \
                if int(reference) < self.steps else missing
        if reference.startswith("AT"):
            return self._bound(source, reference, kind, reference, self.tests[reference]) if reference in self.tests else missing
        if reference.startswith(("AJ", "J")):
            return self._bound(source, reference, kind, reference, self.judgments[reference]) \
                if reference in self.judgments else missing
        return EvidenceReference(source, reference, kind, "valid", reference) if reference in self.unbound else missing


def _listed(items, limit=8):
    items = list(dict.fromkeys(items))
    return ", ".join(items[:limit]) + (f", and {len(items) - limit} more" if len(items) > limit else "")


class EvidenceIntegrity:
    def assess(self, candidate, claims, evidence, judgments, validations, index, *, audits=(), transitions=(),
               independent=True, engine_evidence=()):
        """engine_evidence: (claim_id, status, evidence) updates written by the Engine itself; any other status is
        model-set, whatever its wording."""
        digest = index.digest
        engine_evidence = set(engine_evidence)
        artifacts = {e.artifact_id: e for e in evidence}
        claim_map = {c.claim_id: c for c in claims}
        references, statements = [], []

        def cite(source, pairs):
            found = tuple(index.resolve(source, kind, ref) for kind, ref in pairs)
            references.extend(found)
            return found

        def statement(source, text, found, *, verdict=False):
            bad = [r for r in found if r.status != "valid"]
            history = ["model_claimed"] + (["evidence_referenced"] if found else [])
            executed = [index.artifacts[r.resolved_to] for r in found if r.status == "valid" and r.resolved_to in index.artifacts
                        and index.artifacts[r.resolved_to]["evidence_type"] == "EXECUTED_EVIDENCE"]
            if bad:
                status, reason = "unresolved", "cited evidence does not resolve to this candidate's recorded evidence: " + \
                    _listed(f"{r.reference} ({r.status})" for r in bad)
            elif not found:
                status, reason = "model_claimed", "model judgment; corroboration only, never verification"
            elif not verdict and is_final_scope(text) and any(_get(a.get("contract") or {}, "phase") != "final" for a in executed):
                history.append("evidence_validated")
                status, reason = "unsupported", ("statement about final-task or complete correctness cites development-scope "
                                                 "or undeclared-phase evidence: " + _listed(a["artifact_id"] for a in executed))
            else:
                status, reason = "evidence_validated", ("references resolve to recorded evidence; the statement itself "
                                                        "remains a model statement")
            if history[-1] != status:
                history.append(status)
            statements.append(StatementIntegrity(source, text, status, tuple(history), reason,
                                                 tuple(f"{r.reference}: {r.status}" for r in found)))

        for j in judgments:
            statement(f"{j.judgment_id}.verdict", f"{j.verdict.value}; recommended {j.recommended_action}",
                      cite(f"{j.judgment_id}.evidence", [("artifact", ref) for ref in dict.fromkeys(j.evidence)]), verdict=True)
            for category in ("fatal_issues", "major_issues", "minor_issues"):
                for n, issue in enumerate(getattr(j, category)):
                    source = f"{j.judgment_id}.{category}[{n}]"
                    found = cite(source + ".evidence", [("artifact", ref) for ref in dict.fromkeys(issue.evidence)])
                    found += cite(source, references_in(issue.description))
                    if found:
                        statement(source, issue.description, found)
            for n, text in enumerate(j.uncertainties):
                if references_in(text):
                    statement(f"{j.judgment_id}.uncertainties[{n}]", text, cite(f"{j.judgment_id}.uncertainties[{n}]", references_in(text)))
        for source, text in transitions:
            if references_in(text):
                statement(source, text, cite(source, references_in(text)))

        contradictions = self._contradictions(evidence, judgments, index, claim_map, digest)
        conflicted = {c.target for c in contradictions}
        by_claim = {v.claim_id: v for v in validations}
        claim_results = []
        for claim in claims:
            v = by_claim.get(claim.claim_id)
            model_status = claim.evidence_status.value
            engine_text = (claim.claim_id, model_status, claim.evidence) in engine_evidence
            status_source = "engine" if engine_text else "model" if model_status != "UNVERIFIED" else "none"
            found = () if engine_text else cite(f"{claim.claim_id}.evidence", references_in(claim.evidence))
            bad = [r for r in found if r.status != "valid"]
            supporting = v.supporting_artifacts if v else ()
            contradicting = v.contradicting_artifacts if v else ()
            out = tuple((a, scope_gap(artifacts[a], claim, digest) or "outside declared scope")
                        for a in (v.out_of_scope_artifacts if v else ()) if a in artifacts)
            history = ["model_claimed"] + (["evidence_referenced"] if found else []) + \
                      (["evidence_validated"] if found and not bad else []) + (["checker_supported"] if supporting else [])
            if claim.claim_id in conflicted:
                status, reason = "unresolved", "contradictory evidence or judgments concern this claim"
            elif contradicting:
                status, reason = "unsupported", "a trusted check of this candidate failed: " + _listed(contradicting)
            elif supporting:
                status, reason = "verified", "trusted executed check within its declared scope: " + _listed(supporting)
            elif bad:
                status, reason = "unresolved", "cited evidence does not resolve: " + _listed(f"{r.reference} ({r.status})" for r in bad)
            elif out:
                status, reason = "unsupported", "passed checks do not cover this claim: " + _listed(f"{a} ({why})" for a, why in out)
            elif found:
                status, reason = "evidence_validated", "references resolve, but no trusted check covers this claim"
            else:
                status = "model_claimed"
                reason = ("model-asserted status without trusted evidence" if status_source == "model" else
                          "support recorded for another candidate does not transfer" if status_source == "engine" else
                          "no trusted evidence")
            consensus = consensus_kind(claim.evidence) if status_source == "model" else ""
            if consensus and status != "verified":
                reason += f"; the stated support is {consensus}, which is agreement, not verification"
            if history[-1] != status:
                history.append(status)
            claim_results.append(ClaimIntegrity(claim.claim_id, claim.text, model_status, status_source, status,
                tuple(history), reason, supporting, out, contradicting, tuple(f"{r.reference}: {r.status}" for r in found),
                consensus))

        trusted = tuple({"artifact_id": e.artifact_id, "passed": e.passed, "source": e.source, "targets": list(e.targets),
                         "check_id": e.contract.check_id if e.contract else None,
                         "phase": e.contract.phase if e.contract else "undeclared",
                         "artifact_binding": ("mismatch" if artifact_mismatch(e, digest) else "matches")
                                             if e.contract and e.contract.artifact_sha256 else "undeclared"}
                        for e in evidence if e.evidence_type == "EXECUTED_EVIDENCE")
        verdicts = {j.judgment_id: j.verdict.value for j in judgments}
        agreement = {"judgments": verdicts, "agreement": len(verdicts) > 1 and len(set(verdicts.values())) == 1,
                     "same_model_identity": not independent, "status": "model_claimed",
                     "counts_as": "corroboration only; never independent verification"}
        risks = tuple({"target_id": a.target_id, "audit": a.status, "status": "unresolved",
                       "reason": "an accepted risk is a retained concern; it is not verified"}
                      for a in audits if getattr(a, "transition", "") in ("accepted_risk", "ACCEPTED_RISK") and a.status != "INVALID")

        uncertain = []
        bad_refs = [r for r in references if r.status != "valid"]
        if bad_refs:
            uncertain.append("Unresolved evidence references kept as cited: " +
                             _listed(f"{r.source} -> {r.reference} ({r.status})" for r in bad_refs))
        scoped = [c.claim_id for c in claim_results if c.status == "unsupported" and c.out_of_scope and not c.contradicting]
        scoped += [s.source for s in statements if s.status == "unsupported"]
        if scoped:
            uncertain.append("Evidence used outside its checked scope was not counted: " + _listed(scoped))
        if contradictions:
            uncertain.append("Contradictory evidence or judgments remain unresolved for: " + _listed(c.target for c in contradictions))
        asserted = [f"{c.claim_id} ({c.model_status})" for c in claim_results
                    if c.status_source == "model" and c.model_status in ("SUPPORTED", "NOT_APPLICABLE")
                    and c.status not in ("verified", "unsupported", "unresolved")]
        if asserted:
            uncertain.append("Model-asserted claim status has no trusted evidence: " + _listed(asserted))
        agreed = [f"{c.claim_id} ({c.consensus})" for c in claim_results if c.consensus and c.status != "verified"]
        if agreed:
            uncertain.append("Agreement is recorded as consensus, not verification: " + _listed(agreed))
        mismatched = [t["artifact_id"] for t in trusted if t["artifact_binding"] == "mismatch"]
        if mismatched:
            uncertain.append("Executed evidence checked a different artifact: " + _listed(mismatched))
        # A receipt's existence is not support: a PASS counts only for recorded claims or concerns it targets.
        known = set(claim_map) | set(index.unbound)
        passes = [e for e in evidence if e.evidence_type == "EXECUTED_EVIDENCE" and e.passed and not artifact_mismatch(e, digest)]
        if passes and not any(t in known for e in passes for t in e.targets):
            uncertain.append("Executed checks cover no recorded claim or concern: " + _listed(e.artifact_id for e in passes))
        counts = {}
        for item in (*claim_results, *statements):
            counts[item.status] = counts.get(item.status, 0) + 1
        return IntegrityReport(candidate.candidate_id, digest, tuple(claim_results), tuple(statements), tuple(references),
                               contradictions, trusted, agreement, risks, tuple(uncertain), counts)

    @staticmethod
    def _contradictions(evidence, judgments, index, claims, digest):
        known = set(index.unbound) | {t for e in evidence for t in e.targets}
        supports, opposes = {}, {}
        for e in evidence:
            if e.evidence_type != "EXECUTED_EVIDENCE" or artifact_mismatch(e, digest):
                continue
            for target in e.targets:
                if e.passed and target in claims and scope_gap(e, claims[target], digest):
                    continue  # An out-of-scope PASS is not support, so it cannot be one side of a conflict.
                (supports if e.passed else opposes).setdefault(target, []).append(
                    f"check {e.artifact_id} {'PASS' if e.passed else 'FAIL'}")
        by_id = {e.artifact_id: e for e in evidence}
        for j in judgments:
            for category in ("fatal_issues", "major_issues", "minor_issues"):
                for issue in getattr(j, category):
                    if issue.target in known and issue.decisive:  # a misattributed finding opposes nothing
                        opposes.setdefault(issue.target, []).append(f"{j.judgment_id} {category[:-7]} issue")
            if j.verdict.value == "PASS":
                for ref in j.evidence:
                    for target in getattr(by_id.get(ref), "targets", ()):
                        supports.setdefault(target, []).append(f"{j.judgment_id} PASS citing {ref}")
        return tuple(Contradiction(t, tuple(supports[t]), tuple(opposes[t])) for t in sorted(set(supports) & set(opposes)))


IDENTICAL_CONFLICT = "Contradictory evidence or judgments on byte-identical content remain unresolved"
IDENTICAL_FAILURE = "A trusted check of byte-identical content failed"
_BOUND = "bound to this content by the checker's artifact hash"


def identical_content_findings(records, final_candidate_id, resolved=None):
    """Classify integrity findings recorded for byte-identical candidates other than the returned one.

    records: (step, integrity report data) of candidates whose content is byte-identical to the returned candidate.
    resolved: {target_id: step} of concerns resolved on that content by a transition audited VALID (executed evidence).
    Content-related conflicts (a contradiction about a claim or concern, or a trusted check that failed) concern the
    same bytes. Their applicability is demonstrated only when the failed check binds this exact content; otherwise it
    is undetermined. Either way they stay unresolved; they are never converted into a failure. Citation errors,
    another judge's out-of-scope statements, and candidate-specific process failures are listed, not transferred.
    Returns (applicable, resolved_later, not_transferred, uncertainties)."""
    resolved = resolved or {}
    applicable, resolved_later, not_transferred = [], [], []
    for step, report in records:
        who = report["candidate_id"]
        if who == final_candidate_id:
            continue
        failed = {t["artifact_id"]: t for t in report["trusted_evidence"] if not t["passed"]}
        conflicts = {c["target"] for c in report["contradictions"]}
        items = [{"kind": "contradiction", "target": c["target"], "supporting": c["supporting"], "opposing": c["opposing"],
                  "artifacts": [a for a, t in failed.items() if c["target"] in t["targets"]]} for c in report["contradictions"]]
        items += [{"kind": "failed_check", "target": c["claim_id"], "artifacts": list(c["contradicting"])}
                  for c in report["claims"] if c["contradicting"] and c["claim_id"] not in conflicts]
        for item in items:
            bound = any(failed.get(a, {}).get("artifact_binding") == "matches" for a in item["artifacts"])
            entry = {**item, "candidate_id": who, "step": step, "applicability": "demonstrated: " + _BOUND if bound else
                     "undetermined: judged or checked in another candidate's evaluation of identical content"}
            if resolved.get(item["target"], -1) > step:
                resolved_later.append({**entry, "resolved_at_step": resolved[item["target"]]})
            else:
                applicable.append(entry)

        def listed(category, reason, **fields):
            not_transferred.append({"kind": "evidence_integrity", "category": category, "candidate_id": who, "step": step,
                                    **fields, "reason": reason})
        for r in report["references"]:
            if r["status"] != "valid":
                listed("citation", "a citation made in another candidate's judgment or claim; it concerns that record, "
                       "not the returned content", source=r["source"], reference=r["reference"], status=r["status"])
        for s in report["statements"]:
            if s["status"] == "unsupported":
                listed("statement_scope", "another candidate's judge used evidence outside its scope; the statement "
                       "asserts no defect in the content", source=s["source"])
        for t in report["trusted_evidence"]:
            if t["artifact_binding"] == "mismatch":
                listed("process", "another candidate's check was bound to a different artifact",
                       artifact_id=t["artifact_id"])
        for c in report["claims"]:
            if c["status"] != "verified" and not c["contradicting"] and (c["out_of_scope"] or c["status_source"] == "model"
                    and c["model_status"] in ("SUPPORTED", "NOT_APPLICABLE")):
                listed("claim_status", "a claim status or check mapping in another candidate's scope",
                       claim_id=c["claim_id"], status=c["status"])
    uncertainties = []
    note = lambda f: f["candidate_id"] + "; " + (_BOUND if f["applicability"].startswith("demonstrated")
                                                 else "applicability undetermined")
    conflicts = [f"{f['target']} ({note(f)})" for f in applicable if f["kind"] == "contradiction"]
    if conflicts:
        uncertainties.append(IDENTICAL_CONFLICT + ": " + _listed(conflicts))
    failures = [f"{f['target']} ({', '.join(f['artifacts'])} on {note(f)})" for f in applicable if f["kind"] == "failed_check"]
    if failures:
        uncertainties.append(IDENTICAL_FAILURE + ": " + _listed(failures))
    return applicable, resolved_later, not_transferred, uncertainties


def integrity_summary(report):
    """Scorecard view: everything short of verified stays listed, with its reason."""
    if report is None:
        return None
    data = to_data(report)
    open_items = [{"id": c["claim_id"], "text": c["text"], "status": c["status"], "reason": c["reason"]}
                  for c in data["claims"] if c["status"] != "verified"]
    open_items += [{"id": s["source"], "text": s["text"], "status": s["status"], "reason": s["reason"]}
                   for s in data["statements"] if s["status"] in ("unresolved", "unsupported")]
    return {"candidate_id": report.candidate_id, "status_counts": data["status_counts"],
            "verified_claims": [c["claim_id"] for c in data["claims"] if c["status"] == "verified"],
            "not_verified": open_items,
            "unresolved_references": [r for r in data["references"] if r["status"] != "valid"],
            "contradictions": data["contradictions"], "trusted_evidence": data["trusted_evidence"],
            "model_agreement": data["model_agreement"], "accepted_risks": data["accepted_risks"],
            "blocks_verified_acceptance": list(report.uncertainties)}
