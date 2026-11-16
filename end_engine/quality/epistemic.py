"""Bounded status assertions in final prose/JSON, bound to existing claims and check scope.

This checks earned epistemic status, not arbitrary factual truth. It never makes a
model/consensus statement evidence, executes generated code, or rewrites an answer.
"""
from dataclasses import dataclass
import json
import re

from ..cognition.deduplication import normalize
from .integrity import content_sha256, scope_gap
from ..core.output_format import final_answer_region

STRONG = re.compile(r'\b(?:verif(?:ied|ies|y)|confirm(?:ed|s|ing)?|establish(?:ed|es)?|prove[sdn]?|'
                    r'certain|demonstrat(?:ed|es)|validat(?:ed|es))\b', re.I)
NEGATION = re.compile(r"\b(?:not(?! only\b| just\b)|never|cannot|can't|could not|couldn't|does not|doesn't|no)\b[^.;,]{0,45}$", re.I)
UNIVERSAL = re.compile(r'\b(?:universally|always|everywhere|all possible|without exception)\b', re.I)
STATUS_KEYS = frozenset(('certainty', 'confidence', 'status', 'verification', 'verified', 'confirmed'))


@dataclass(frozen=True)
class EpistemicClaim:
    target: str
    declared_status: str
    location: str
    statement: str


def answer_region(content):
    return final_answer_region(content)


def extract_epistemic_claims(content):
    """At most 32 status assertions, depth <= 5; code literals are not prose assertions."""
    region = answer_region(content)
    claims = []
    exhausted = len(region) > 32000
    if exhausted:
        region = region[:32000]
    def add(target, status, path, statement):
        nonlocal exhausted
        if len(claims) < 32:
            claims.append(EpistemicClaim(target[:1500], status, path, statement[:1500]))
        else:
            exhausted = True
    def visit(value, path='$', inherited='', depth=0):
        nonlocal exhausted
        if depth > 5 or len(claims) >= 32:
            exhausted = True
            return
        if isinstance(value, dict):
            exhausted = exhausted or len(value) > 64
            targets = [value.get(k) for k in ('claim', 'conclusion', 'statement', 'root_cause', 'answer', 'target')]
            target = next((s for s in targets if isinstance(s, str) and s.strip()), None)
            target = target or next((s for k, s in value.items() if k.lower() not in STATUS_KEYS
                                   and isinstance(s, str) and s.strip()), inherited)
            for key, item in list(value.items())[:64]:
                if key.lower() in STATUS_KEYS:
                    status = ('verified' if item is True and key.lower() in ('verified', 'confirmed', 'verification')
                              else 'certain' if type(item) in (int, float) and item == 1 and key.lower() == 'confidence'
                              else str(item) if isinstance(item, str) else '')
                    status_words = status.replace('_', ' ').replace('-', ' ')
                    for match in STRONG.finditer(status_words):
                        if not NEGATION.search(status_words[:match.start()]):
                            add(target or '[unspecified claim]', match[0].lower(), path + '.' + key,
                                (target or '[unspecified claim]') + ' [' + key + '=' + status + ']')
                if isinstance(item, (dict, list)):
                    visit(item, path + '.' + key, target, depth + 1)
        elif isinstance(value, list):
            exhausted = exhausted or len(value) > 64
            for i, item in enumerate(value[:64]):
                visit(item, path + f'[{i}]', inherited, depth + 1)
    blocks = re.findall(r'```(?:json)?\s*\n(.*?)```', region, re.S | re.I)
    exhausted = exhausted or len(blocks) > 8
    parsed = False
    for block in blocks[:8] or [region.strip()]:
        try:
            obj = json.loads(block)
        except (ValueError, RecursionError):
            continue
        if isinstance(obj, (dict, list)):
            visit(obj)
            parsed = True
    prose = re.sub(r'```.*?```', '', region, flags=re.S)
    if parsed and not blocks:
        prose = ''
    for clause in re.split(r'(?<=[.!?;])\s+|\n+|\bbut\b|\bhowever\b', prose, flags=re.I):
        if (re.fullmatch(r'\s*["\u201c].*["\u201d]\s*', clause) or re.search(
                r'\b(?:the user|the task|the prompt|a judge|the model|the report)\s+'
                r'(?:claims?|says?|states?|wrote|alleges?)\b', clause, re.I)):
            continue
        for match in STRONG.finditer(clause):
            prefix = clause[:match.start()]
            if NEGATION.search(prefix) or re.search(r'\b(?:if|whether|could|might|may|would|should|suppose|hypothetical|hypothetically)\b', prefix, re.I):
                continue
            active = bool(re.fullmatch(r'confirms?|verifies|establishes?|proves?|demonstrates|validates', match[0], re.I))
            if not active and not re.search(r'\b(?:is|are|was|were|been|has|have|i|we|engineers?|judges?|models?)\b', prefix, re.I):
                continue
            target = re.sub(r'\b(?:is|are|was|were|has been|have been|independently)\s*$', '', prefix.strip(), flags=re.I)
            suffix = clause[match.end():].strip(' .:')
            if suffix:
                if active or re.fullmatch(r'(?:i|we)(?: have)?(?: independently)?', prefix.strip(), re.I):
                    target = ''
                target += ' ' + suffix
            add(target.strip(), match[0].lower(), 'prose', clause.strip())
    for match in re.finditer(r'\b(?:check|test)\s+([\w.-]+)\s+passed\s+([^.;\n]+)', prose, re.I):
        prefix = prose[max(0, match.start()-80):match.start()]
        if not NEGATION.search(prefix) and not re.search(r'\b(?:if|could|might|would|user claims)\b', prefix, re.I):
            add(match[0], 'passed', 'executed_check', match[0])
    if exhausted:
        claims.append(EpistemicClaim('[scan limit]', 'unassessed', 'scan_limit',
                      'Output exceeds bounded epistemic inspection; shorten before return'))
    return tuple(claims)


def epistemic_integrity(content, candidate_id, claims=(), evidence=(), *, inspected_answer=None):
    """The ceiling is UNVERIFIED unless an exact targeted check supports this assertion's scope."""
    results = []
    digest = content_sha256(content)
    for assertion in extract_epistemic_claims(inspected_answer if inspected_answer is not None else content):
        matched = [c for c in claims if normalize(c.text) in (normalize(assertion.target), normalize(assertion.statement))]
        support, contradict = [], []
        universal = bool(UNIVERSAL.search(assertion.statement))
        for claim in matched:
            for artifact in evidence:
                contract = artifact.contract
                if (universal or artifact.evidence_type != 'EXECUTED_EVIDENCE'
                        or artifact.candidate_id != candidate_id or claim.claim_id not in artifact.targets
                        or contract is None or not contract.claims or contract.artifact_sha256 != digest
                        or scope_gap(artifact, claim, digest)):
                    continue
                if contract.bounds and normalize(contract.bounds) not in normalize(assertion.target):
                    continue
                (support if artifact.passed else contradict).append(artifact.artifact_id)
        established = bool(support) and not contradict
        results.append({'candidate_id': candidate_id, 'target': assertion.target, 'statement': assertion.statement,
                        'declared_status': assertion.declared_status, 'location': assertion.location,
                        'supported_status': 'VERIFIED_WITHIN_SCOPE' if established else 'UNVERIFIED',
                        'claim_ids': [c.claim_id for c in matched], 'supporting_artifacts': list(dict.fromkeys(support)),
                        'contradicting_artifacts': list(dict.fromkeys(contradict)),
                        'overclaim': not established, 'provenance': 'ENGINE_DERIVED',
                        'reason': 'conflicting scoped executed evidence remains unresolved' if contradict else
                                  'targeted executed support within declared scope' if established else
                                  'no candidate-bound executed support for this assertion and scope'})
    return tuple(results)
