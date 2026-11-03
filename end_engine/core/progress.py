"""Cheap internal cycle progress, measured after rollback. No external scores or model calls."""
import ast
import json
import re
import hashlib
from .output_format import final_answer_region


def substantive_text(text):
    # Ignore observable in-band deliberation and punctuation/filler; retain negation,
    # numbers and operators. This deliberately does not infer arbitrary equivalence.
    text = final_answer_region(text)
    # Structured ordering and code formatting must not hide/introduce progress.
    # AST parsing inspects syntax as data; it never executes candidate code.
    for language, block in re.findall(r'```(json|python)\s*\n(.*?)```', text, re.S | re.I):
        try:
            parsed = (json.dumps(json.loads(block), sort_keys=True, separators=(',', ':'), allow_nan=False)
                      if language.lower() == 'json' else ast.dump(ast.parse(block), include_attributes=False))
        except (ValueError, SyntaxError, RecursionError):
            continue
        text = text.replace(block, hashlib.sha256(parsed.encode()).hexdigest())
    words = re.findall(r'[a-z_]\w*|\d+(?:\.\d+)?|[<>=+\-]', text.lower())
    return tuple(w for w in words if w not in {'a', 'an', 'the', 'indeed', 'clearly', 'basically'})


class InternalProgress:
    def __init__(self, trajectory, patience=2):
        self.trajectory, self.patience = trajectory, patience
        self.previous, self.last_cycle, self.stagnant = None, -1, 0

    def observe(self, cycle, state, blockers=()):
        if cycle <= self.last_cycle:
            return False
        reasons = [name for name, value in state.items() if self.previous is not None and value != self.previous[name]]
        if cycle and self.previous is not None:
            self.stagnant = 0 if reasons else self.stagnant + 1
            self.trajectory.record('cycle_progress', {'cycle': cycle, 'reasons': reasons,
                'no_progress_cycles': self.stagnant, 'blockers': list(blockers)}, 'cycle_progress')
        self.previous, self.last_cycle = state, cycle
        self.trajectory.set('no_progress_cycles', self.stagnant)
        return self.stagnant >= self.patience and not blockers


def progress_state(candidate, registry, cognitive, verification, gate=None, evidence=(), integrity=None, branches=()):
    normalize = lambda text: substantive_text(text or '')
    issues = tuple(sorted((normalize(w.description), w.severity, w.status.value)
                          for w in registry.snapshot() if w.decisive))
    claims = (tuple(sorted((normalize(c.text), c.status) for c in integrity.claims
                          if c.status in ('verified', 'checker_supported', 'unsupported'))) if integrity is not None else
              tuple(sorted((normalize(c.text), c.evidence_status.value) for c in cognitive.knowledge.claims.values()
                           if c.evidence_status.value != 'UNVERIFIED')))
    checks = tuple(sorted((e.evidence_type, e.passed, normalize(e.description),
                           tuple(e.contract.properties) if e.contract else ()) for e in evidence
                          if e.evidence_type == 'EXECUTED_EVIDENCE'))
    assumptions = tuple(sorted((normalize(a.statement), a.status.value) for a in cognitive.knowledge.assumptions.values()
                               if a.decisive))
    return {'candidate_content': normalize(candidate.content), 'issue_state': issues, 'claim_support_state': claims,
            'assumption_state': assumptions, 'evidence_state': checks,
            'verifier_state': (verification.passed, tuple(sorted(normalize(s) for s in verification.remaining_issues)))
                              if verification and verification.assessment_decisive else None,
            'quality_gate_state': gate.decision.value if gate else None,
            'branch_state': tuple(sorted((normalize(b.content), b.status) for b in branches)),
            'contradiction_state': tuple(sorted((normalize(c.target), c.resolution,
                                      bool(c.supporting), bool(c.opposing)) for c in integrity.contradictions)) if integrity else ()}
