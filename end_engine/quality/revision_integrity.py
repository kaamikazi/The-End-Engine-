"""Bounded citation/receipt checks. Registration is not proof that a world claim is true."""
import json
import re
from ..core.output_format import candidate_answer
from .integrity import content_sha256, references_in


def registered_references(task, contract=None, evidence=()):
    declared = set(getattr(contract, 'reference_ids', ()))
    # Reference declarations, not arbitrary bracket strings appearing in candidate prose.
    declared.update(re.findall(r'(?m)^\s*\[([\w.-]{1,80})\]\s*\S', task))
    declared.update(e.artifact_id for e in evidence)
    declared.update(e.source for e in evidence)
    for e in evidence:
        declared.update(value for _, value in references_in(e.source))
        if e.contract:
            declared.add(e.contract.check_id)
            if e.contract.artifact_sha256:
                declared.add(e.contract.artifact_sha256)
    return declared


def citation_claims(content):
    """Only explicit reference fields/source-use assertions; hypothetical sources remain discussable."""
    result = []
    blocks = re.findall(r'```(?:json)?\s*\n(.*?)```', content, re.S | re.I)[:8]
    def visit(value, depth=0):
        if depth > 5:
            return
        if isinstance(value, dict):
            for key, val in list(value.items())[:64]:
                if key.lower() in ('evidence_used', 'citations', 'references', 'sources') and isinstance(val, list):
                    result.extend((str(x), 'citation_field') for x in val[:64] if isinstance(x, str))
                elif isinstance(val, (dict, list)):
                    visit(val, depth+1)
        elif isinstance(value, list):
            for val in value[:64]:
                visit(val, depth+1)
    for block in blocks or [content.strip()]:
        try:
            visit(json.loads(block))
        except (ValueError, RecursionError):
            continue
    for clause in re.split(r'(?<=[.;])\s+|\n+', content[:32000]):
        if re.search(r'\b(?:if|could|may|might|possible|hypothetical|consider|user claims|user says)\b', clause, re.I):
            continue
        match = re.search(r'\baccording to\s+([^,.;\n]{1,80})[,;]', clause, re.I)
        if match and re.search(r'\b(?:confirm\w*|verif\w*|establish\w*|prov\w*)\b', clause, re.I):
            result.append((match[1].strip(), 'source_authority'))
    return tuple(dict.fromkeys(result))[:64]


def evidence_violations(task, candidate, evidence=(), contract=None):
    answer = candidate_answer(candidate)
    known = registered_references(task, contract, evidence)
    closed = bool(getattr(contract, 'reference_ids', ())) or bool(re.search(
        r'cite only|only (?:the )?(?:provided|available|registered) (?:evidence|reference|source)|'
        r'evidence_used.{0,100}evidence IDs', task, re.I | re.S))
    violations = []
    for ref, kind in citation_claims(answer):
        normalized = ref.strip(' []')
        if ref in known or normalized in known:
            continue
        if closed or kind == 'source_authority':
            violations.append({'candidate_id': candidate.candidate_id,
                'type': 'unsupported_reference' if kind == 'citation_field' else 'unregistered_source_authority',
                'reference': ref, 'source_origin': 'ENGINE_DERIVED', 'decisive': True,
                'description': f'Reference {ref!r} is not in the declared/registered evidence set; '
                               'END has no authority to treat it as independently verified',
                'scope': 'reference registration only; no claim that the external source does not exist'})
    return tuple(violations)


def evidence_delta(task, parent, candidate, evidence=(), previous_evidence=(), contract=None):
    before = citation_claims(candidate_answer(parent)) if parent else ()
    after = citation_claims(candidate_answer(candidate))
    old = registered_references(task, contract, previous_evidence)
    new = registered_references(task, contract, evidence)
    return {'candidate_id': candidate.candidate_id,
            'parent_candidate_id': parent.candidate_id if parent else None,
            'artifact_sha256': content_sha256(candidate_answer(candidate)),
            'raw_response_sha256': content_sha256(candidate.content),
            'evidence_before': sorted(old), 'evidence_after': sorted(new),
            'new_registered_evidence': sorted(new-old),
            'citation_additions': [r for r in after if r not in before],
            'citation_removals': [r for r in before if r not in after],
            'violations': evidence_violations(task, candidate, (*previous_evidence, *evidence), contract),
            'source_origin': 'ENGINE_DERIVED', 'model_calls': 0}
