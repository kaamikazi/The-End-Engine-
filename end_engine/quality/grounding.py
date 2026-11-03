"""Candidate-grounded judge findings (v0.3.5). Deterministic; no model is called.

A judge's finding about the candidate must resolve to the candidate. TASK text is user-provided (it may contain false
premises) and is never candidate content; a judge's statement is MODEL_JUDGMENT, never verified fact.

Grounding statuses:
  GROUNDED                     the finding's candidate_quote occurs in the candidate
  UNQUOTED                     no quote given and nothing contradicts attribution (pre-0.3.5 behaviour)
  TASK_CONSTRAINT              the finding is about a stated task requirement (checked against the task, not here)
  MISATTRIBUTED                text attributed to the candidate occurs only in the TASK
  UNGROUNDED                   the declared candidate_quote occurs neither in the candidate nor in the task
  TASK_PREMISE_DEPENDENT       the objection rests on an assertion made by the task (a premise, not a verified fact)
  REQUIRES_EXTERNAL_VALIDATION an EXTERNAL_FACT claim with no executed evidence of this candidate cited
v0.3.5.1 separates textual annotations from semantic support. SEMANTIC_SUPPORTED
requires a scoped executed check; SEMANTIC_CONTRADICTED and SEMANTIC_UNSUPPORTED
are nondecisive. A quote alone does not prove a behavioral interpretation.
A non-decisive finding stays visible as uncertainty; it can never by itself cause
REJECT, REVISE, rollback or a high-severity weakness. Real candidate defects, task-constraint violations and failed
executed checks keep their full effect."""
from dataclasses import dataclass, replace
import re

from .state import Provenance
from ..core.task_contract import TaskContract, assertion_kind
from .integrity import content_sha256

DECISIVE = ("GROUNDED", "UNQUOTED", "TASK_CONSTRAINT", "SEMANTIC_SUPPORTED")
MIN_SPAN = 12  # characters; shorter backtick spans (keywords, names) are too ambiguous to attribute

_SPAN = re.compile(r"`([^`\n]{%d,})`" % MIN_SPAN)
# The finding contrasts what the candidate states with what the task states (task wording used as the yardstick).
_CONTRAST = re.compile(r"\bcandidate\b[^.;]{0,80}\b(?:claims?|states?|says|asserts?|argues?)\b[^;]{0,240}?\bbut\b[^.;]{0,60}"
                       r"\b(?:problem|task|prompt|question|premise|user)\b", re.I)
# A sentence that cites the task's own assertion as the basis ("the problem statement explicitly states ...").
_TASK_ASSERTION = re.compile(r"\b(?:problem(?: statement)?|task(?: statement| description)?|prompt|premise)\b[^.;]{0,30}"
                             r"\b(?:explicitly\s+)?(?:states?|says|claims?|asserts?|assumes?|stipulates?)\b", re.I)
_CONSTRAINT = re.compile(r"\b(?:format|json|csv|code block|field|key|schema|output|word limit|length|"
                         r"instructions?|instructed|asks? for|requested)\b", re.I)


def _norm(text):
    return re.sub(r"\s+", " ", (text or "").replace("`", "").strip().strip("\"'")).lower()


@dataclass(frozen=True)
class Grounding:
    status: str
    decisive: bool
    reason: str
    provenance: str = Provenance.MODEL_JUDGMENT.value
    textual: str = "UNQUOTED"
    semantic: str = "UNASSESSED"


def _proposition(text):
    """Only explicit polarity of otherwise identical propositions, not arbitrary entailment."""
    value = _norm(text)
    negative = bool(re.search(r"\b(?:not|never|cannot|can't|fails? to)\b", value))
    value = re.sub(r"\b(?:does not|do not|did not|not|never|cannot|can't|fails? to)\b", "", value)
    value = re.sub(r"\b(?:is|are|was|were|does|do|did)\b", "", value)
    value = re.sub(r"\b(raises|returns|rejects|accepts|preserves)\b", lambda m: m[0][:-1], value)
    return re.sub(r"[^\w]+", " ", value).strip(), negative


def _scoped_semantics(issue, content, evidence, candidate_id):
    source, defect = _proposition(issue.source_claim), _proposition(issue.alleged_defect)
    if not source[0] or source[0] != defect[0] or source[1] == defect[1]:
        return None
    outcomes = []
    for artifact in evidence:
        contract = artifact.contract
        if (artifact.evidence_type != "EXECUTED_EVIDENCE" or artifact.candidate_id != candidate_id or
                contract is None or contract.artifact_sha256 != content_sha256(content)):
            continue
        # A trusted checker explicitly declares this proposition and exact artifact.
        declared = (*contract.claims, *contract.properties)
        matches_source = any(_proposition(s) == source for s in declared)
        matches_defect = any(_proposition(s) == defect for s in declared)
        if not matches_source and not matches_defect:
            continue
        if contract.bounds and _norm(contract.bounds) not in _norm(issue.source_claim + ' ' + issue.alleged_defect):
            continue
        defect_supported = (matches_defect and artifact.passed) or (matches_source and not artifact.passed)
        outcomes.append((defect_supported, artifact.artifact_id, contract.check_id))
    if len({o[0] for o in outcomes}) > 1:
        return ('SEMANTIC_UNSUPPORTED', False, 'conflicting scoped executed checks remain unresolved: '
                + ', '.join(o[1] for o in outcomes))
    if outcomes:
        supported = outcomes[0][0]
        return ('SEMANTIC_SUPPORTED' if supported else 'SEMANTIC_CONTRADICTED', supported,
                'scoped executed checks ' + ', '.join(o[1] for o in outcomes) +
                (' establish the defect' if supported else ' contradict the defect'))
    return None


def _ground_issue(issue, task, candidate_content, executed_ids=(), *, evidence=(), candidate_id=None, contract=None,
                  artifact_content=None):
    """Classify one judge finding against the TASK, the CANDIDATE and executed evidence."""
    candidate, task_text = _norm(candidate_content), _norm(task)
    quote = _norm(issue.candidate_quote)
    textual = "GROUNDED" if quote and quote in candidate else "UNQUOTED"
    def result(status, decisive, reason):
        return Grounding(status, decisive, reason, textual=textual, semantic=status)
    if quote and quote not in candidate:
        status = "MISATTRIBUTED" if quote in task_text else "UNGROUNDED"
        return Grounding(status, False, "candidate_quote is not candidate content", textual=status, semantic="UNSUPPORTED")
    scoped = _scoped_semantics(issue, artifact_content or candidate_content, evidence, candidate_id)
    if scoped:
        return result(*scoped)
    reference = issue.task_reference
    prescriptive = assertion_kind(task, reference, contract) == "PRESCRIPTIVE_TASK_CONSTRAINT"
    if issue.claim_type == "TASK_CONSTRAINT" and prescriptive:
        return result("TASK_CONSTRAINT", True, "explicit prescriptive task requirement, not a world-fact assertion")
    for span in _SPAN.findall(issue.description or ""):
        span = _norm(span)
        if span and span not in candidate and span in task_text:
            return result("MISATTRIBUTED", False, f"quoted text occurs only in the task: `{span[:80]}`")
    description = (issue.description or "") + ' ' + issue.basis
    relies_on_task = bool(issue.task_reference.strip()) and issue.claim_type != "CANDIDATE_INTERNAL"
    contrast = _CONTRAST.search(description) and not _CONSTRAINT.search(description)  # format/output = a constraint
    premise = relies_on_task or contrast or any(
            _TASK_ASSERTION.search(s) and not _CONSTRAINT.search(s) for s in re.split(r"(?<=[.;])\s+", description))
    premise = premise or bool(re.search(r"\b(?:contradict\w*|conflict\w*)[^.]{0,80}(?:task|problem|prompt).{0,30}premise", description, re.I))
    if premise and not prescriptive:
        return result("TASK_PREMISE_DEPENDENT", False,
                      "descriptive/ambiguous TASK_PROVIDED assertion is not independent factual evidence")
    if issue.claim_type == "TASK_CONSTRAINT" and not prescriptive:
        return result("SEMANTIC_UNSUPPORTED", False, "judge has not identified a prescriptive task requirement")
    if issue.claim_type in ("EXTERNAL_FACT", "EXTERNAL_FACTUAL"):
        # Legacy direct callers may supply already scoped IDs. QualitySession always supplies full artifacts.
        if not evidence and set(issue.evidence) & set(executed_ids):
            return result(textual, True, "legacy caller supplied scoped executed IDs")
        return result("REQUIRES_EXTERNAL_VALIDATION", False, "no executed evidence establishing this factual objection in scope")
    mixed_source = re.search(r"\b(original|task)\b.*\b(corrected|fixed)\b", description, re.I | re.S) and re.search(
        r"contradict|inconsisten", description, re.I)
    behavioral = bool(re.search(r"```python|\bdef\s+\w+\s*\(", candidate_content)) and bool(re.search(
        r"\b(function|code|loop)\b.*\b(handle|raise|return|skip|drop|stop|check|incorrect|bug)", description, re.I | re.S))
    if mixed_source or behavioral or issue.source_claim or issue.alleged_defect or issue.basis:
        return result("SEMANTIC_UNSUPPORTED", False, "quote existence does not establish this interpretation; scoped support is missing")
    return result(textual, True, "legacy finding has no detected external/premise or behavioral inference; remains model judgment")


def ground_issue(issue, task, candidate_content, executed_ids=(), *, evidence=(), candidate_id=None, contract=None):
    from .assessment import AssessmentAuthorityPolicy
    return AssessmentAuthorityPolicy(task, contract).ground(issue, candidate_content, candidate_id,
                                                           evidence=evidence, executed_ids=executed_ids)


def ground_judgment(judgment, task, candidate_content, executed_ids=(), **context):
    """Return the judgment with every issue annotated, plus the list of non-decisive findings."""
    incidents, groups = [], {}
    for category in ("fatal_issues", "major_issues", "minor_issues"):
        annotated = []
        for n, issue in enumerate(getattr(judgment, category)):
            g = ground_issue(issue, task, candidate_content, executed_ids, **context)
            annotated.append(replace(issue, grounding=g.status, decisive=g.decisive,
                                     textual_grounding=g.textual, semantic_grounding=g.semantic))
            if not g.decisive:
                incidents.append({"judgment_id": judgment.judgment_id, "candidate_id": judgment.candidate_id,
                                  "issue": f"{category}[{n}]", "severity": category[:-7], "status": g.status,
                                  "reason": g.reason, "description": issue.description,
                                  "candidate_quote": issue.candidate_quote, "claim_type": issue.claim_type,
                                  "provenance": g.provenance, "textual_grounding": g.textual,
                                  "semantic_grounding": g.semantic, "source_claim": issue.source_claim,
                                  "alleged_defect": issue.alleged_defect, "basis": issue.basis})
        groups[category] = tuple(annotated)
    return replace(judgment, **groups), incidents


def ungrounded_objection(judgment):
    """True when the judgment objects, every fatal/major issue it raised is non-decisive, and it raised at least one.
    Such a judgment's negative verdict, action and scores cannot drive REJECT/REVISE on their own."""
    serious = (*judgment.fatal_issues, *judgment.major_issues)
    return bool(serious) and not any(i.decisive for i in serious)
