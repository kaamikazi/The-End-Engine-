"""One run-local authority boundary for model assessments and deterministic findings.

Models propose, the Engine assigns origin and validates scope. Advisory concerns stay
available for exploration; they cannot prove a defect, close a grounded concern, or
acquire authority through plans, reconciliation or repetition.
"""
from dataclasses import dataclass, replace
from types import SimpleNamespace
import re
from ..core.output_format import candidate_answer, final_answer_region, format_violations, task_requirements
from ..core.task_contract import TaskContract, assertion_kind
from ..core.state import to_data
from .state import Provenance, JudgeIssue
from .revision_integrity import evidence_violations
from .integrity import artifact_mismatch, content_sha256


@dataclass(frozen=True)
class AssessmentFinding:
    finding_id: str
    producer: str
    source_origin: str
    finding_type: str
    target_candidate_id: str
    alleged_defect: str
    rationale: str
    evidence_refs: tuple[str, ...] = ()
    evidence_scope: str = ''
    grounding_status: str = 'UNASSESSED'
    authority_status: str = 'ADVISORY'
    policy_disposition: str = 'INVESTIGATE'
    target_claim_id: str | None = None
    quoted_candidate_span: str = ''
    decisive: bool = False
    premise_origin: str = 'UNKNOWN'


class AssessmentAuthorityPolicy:
    def __init__(self, task, contract=None, trajectory=None):
        self.task, self.contract, self.trajectory = task, contract or TaskContract(), trajectory
        self.evidence = {}
        self._counter = 0

    def record(self, producer, origin, kind, candidate_id, defect, rationale, *, refs=(), scope='',
               grounding='UNSUPPORTED', decisive=False, quote='', premise_origin='UNKNOWN'):
        self._counter += 1
        finding = AssessmentFinding(f'AF{self._counter:04d}', producer, origin, kind, candidate_id,
            defect, rationale, tuple(refs), scope, grounding,
            'VALIDATED_WITHIN_SCOPE' if decisive else 'ADVISORY',
            'ACTIONABLE' if decisive else 'REQUIRES_EVIDENCE', quoted_candidate_span=quote, decisive=decisive,
            premise_origin=premise_origin)
        if self.trajectory is not None:
            self.trajectory.record('assessment_finding', finding, 'assessment_findings')
        return finding

    def ground(self, issue, content, candidate_id, *, evidence=(), executed_ids=(), raw_content=None):
        from .grounding import Grounding, _ground_issue, _proposition, _scoped_semantics
        answer = final_answer_region(content)
        candidate = SimpleNamespace(content=raw_content or content, answer_content=answer,
                                    candidate_id=candidate_id)
        violations = evidence_violations(self.task, candidate, evidence, self.contract)
        text = issue.description+' '+issue.alleged_defect
        if violations and re.search(r'citation|reference|evidence|source', text, re.I):
            relevant = [v for v in violations if v['reference'] in text or v['reference'] in issue.candidate_quote]
            if relevant:
                return Grounding('TASK_CONSTRAINT', True, relevant[0]['description'],
                                 textual='GROUNDED', semantic='DETERMINISTIC_REFERENCE_CHECK')
        formats = format_violations(self.task, content, self.contract)
        if formats and re.search(r'json|format|fence|code block|required value|external librar|external module', text, re.I):
            return Grounding('TASK_CONSTRAINT', True, '; '.join(formats),
                             textual='GROUNDED', semantic='DETERMINISTIC_FORMAT_CHECK')
        g = _ground_issue(issue, self.task, answer, executed_ids, evidence=evidence,
                         candidate_id=candidate_id, contract=self.contract,
                         artifact_content=raw_content or content)
        if not issue.source_claim:
            # Verifiers/critics may only supply a sentence, unlike typed judges.
            # Match literal checker propositions and polarity, not arbitrary entailment.
            proposed = _proposition(issue.alleged_defect or issue.description)
            declarations = [p for e in evidence if e.contract for p in (*e.contract.properties, *e.contract.claims)]
            for declaration in declarations:
                declared = _proposition(declaration)
                if proposed[0] == declared[0] and proposed[1] != declared[1]:
                    scoped = _scoped_semantics(replace(issue, source_claim=declaration,
                        alleged_defect=issue.alleged_defect or issue.description), raw_content or content,
                        evidence, candidate_id)
                    if scoped:
                        return Grounding(*scoped, textual=g.textual, semantic=scoped[0])
        if g.status == 'TASK_CONSTRAINT':
            states = {'online':'offline', 'offline':'online', 'enabled':'disabled',
                      'disabled':'enabled', 'available':'unavailable', 'unavailable':'available'}
            pattern = r'([\w ]{1,80})\s+(?:is|are)\s+(online|offline|enabled|disabled|available|unavailable)\b'
            prescribed = re.search(pattern, issue.task_reference.lower())
            quoted = issue.candidate_quote or answer
            subject = lambda s: re.sub(r'^(?:the|a|an)\s+', '', s.strip())
            if prescribed and any(subject(m[1]) == subject(prescribed[1]) and
                    m[2] == states[prescribed[2]] for m in re.finditer(pattern, quoted.lower())):
                return g
            # Caller-declared resource prohibition, not an inferred world fact.
            unavailable = re.fullmatch(r'([\w ]{1,60}) unavailable', issue.task_reference.strip(), re.I)
            if unavailable and issue.task_reference in self.contract.prescriptive_constraints:
                for m in re.finditer(r'\b(?:use|requires?)\s+(?:the |a |an )?'+re.escape(unavailable[1])+r'\b', answer, re.I):
                    if not re.search(r'\b(?:not|never|if|could|may|might)\b', answer[max(0,m.start()-40):m.start()], re.I):
                        return g
        # A declared requirement is authoritative; a model's allegation that it
        # was violated still needs a mechanical/scoped basis, not just that label.
        if g.decisive and g.status != 'SEMANTIC_SUPPORTED':
            return Grounding('SEMANTIC_UNSUPPORTED', False,
                'assessment proposes a defect; no deterministic or scoped evidence establishes it',
                textual=g.textual, semantic='SEMANTIC_UNSUPPORTED')
        return g

    def issue(self, issue, candidate, producer='judge', origin=Provenance.MODEL_JUDGMENT.value):
        evidence = self.evidence.get(candidate.candidate_id, ())
        g = self.ground(issue, candidate_answer(candidate), candidate.candidate_id,
                        evidence=evidence, raw_content=candidate_answer(candidate))
        if g.semantic in ('DETERMINISTIC_REFERENCE_CHECK', 'DETERMINISTIC_FORMAT_CHECK'):
            issue = replace(issue, description=g.reason, alleged_defect=g.reason)
        premise = ('TASK_ASSERTION' if g.status == 'TASK_PREMISE_DEPENDENT' else
                   'TASK_INSTRUCTION' if g.status == 'TASK_CONSTRAINT' else 'CANDIDATE' if issue.candidate_quote else 'UNKNOWN')
        finding = self.record(producer, origin, issue.category, candidate.candidate_id,
            issue.alleged_defect or issue.description, g.reason, refs=issue.evidence,
            scope=issue.task_reference, grounding=g.status, decisive=g.decisive, quote=issue.candidate_quote,
            premise_origin=premise)
        return replace(issue, grounding=g.status, decisive=g.decisive,
                       textual_grounding=g.textual, semantic_grounding=g.semantic), finding

    def critique(self, output, candidate):
        normalized = {**output, 'findings': []}
        for item in output['findings']:
            issue = JudgeIssue(item['type'], item['description'], evidence=(item['evidence'],),
                               basis=item['evidence'])
            _, finding = self.issue(issue, candidate, 'critique', Provenance.MODEL_CRITIQUE.value)
            normalized['findings'].append({**item, '_assessment': to_data(finding)})
        # Proposed support remains a model statement. It is not evidence of a
        # world claim; existing tool validators own support transitions.
        normalized['claims'] = [{**c, 'evidence_status': 'UNVERIFIED'} for c in output.get('claims', [])]
        normalized['claim_updates'] = []
        for update in output.get('claim_updates', []):
            self.record('claim_update', Provenance.MODEL_CRITIQUE.value, 'claim_support',
                        candidate.candidate_id, str(update), 'model status update is advisory, not executed support')
        normalized['assumptions'] = []
        for item in output.get('assumptions', []):
            finding = self.record('assumption', Provenance.MODEL_CRITIQUE.value, 'hypothesis',
                candidate.candidate_id, item['statement'], 'proposed assumption, not a factual task constraint')
            normalized['assumptions'].append({**item, 'status': 'UNTESTED', '_assessment': to_data(finding)})
        normalized['assumption_updates'] = []
        for update in output.get('assumption_updates', []):
            self.record('assumption_update', Provenance.MODEL_CRITIQUE.value, 'assumption_support',
                candidate.candidate_id, str(update), 'support requires a validated transition, not model assertion')
        return normalized

    def verification(self, result, candidate, registry):
        self.record('verification_summary', Provenance.MODEL_JUDGMENT.value, 'quality_estimate',
                    candidate.candidate_id, f'passed={result.passed}; score={result.score}',
                    'model evaluation is not executed evidence')
        deciding, advisory, requires = [], [], False
        for text in result.remaining_issues:
            _, finding = self.issue(JudgeIssue('verification', text), candidate, 'verification')
            (deciding if finding.decisive else advisory).append(text)
            requires |= not finding.decisive and finding.grounding_status not in (
                'TASK_PREMISE_DEPENDENT', 'MISATTRIBUTED', 'UNGROUNDED', 'SEMANTIC_CONTRADICTED')
        updates = []
        for update in result.weakness_updates:
            item = next(w for w in registry.snapshot() if w.id == update.id)
            evidence = self.evidence.get(candidate.candidate_id, ())
            supported = any(e.evidence_type == 'EXECUTED_EVIDENCE' and e.passed and
                e.candidate_id == candidate.candidate_id and item.id in e.targets and
                not artifact_mismatch(e, content_sha256(candidate_answer(candidate))) for e in evidence)
            # Nondecisive concerns may be retired as bookkeeping, never as proof.
            if not item.decisive or supported:
                updates.append(update)
            else:
                self.record('verification_update', Provenance.MODEL_JUDGMENT.value, 'status_transition',
                    candidate.candidate_id, update.reason, 'grounded concern needs matching trusted support')
        return replace(result, assessment_decisive=bool(deciding), remaining_issues=tuple(deciding),
                       advisory_issues=tuple(advisory), weakness_updates=tuple(updates),
                       assessment_requires_evidence=requires or not result.passed and not result.remaining_issues)

    def plan(self, plan, candidate):
        changes = []
        for change in plan.changes:
            origin = change.source_origin
            conflict = (origin != Provenance.ENGINE_DERIVED.value and bool(re.search(
                r'\b(?:ignore|disregard|override|omit|drop|instead of)\b.{0,80}\b(?:json|format|requirement|constraint)\b|'
                r'\b(?:answer|respond)\b.{0,25}\bprose\b', change.action, re.I)) and
                bool(re.search(r'\bjson\b', self.task, re.I)))
            if origin != Provenance.ENGINE_DERIVED.value:
                conflict |= bool(re.search(r'\b(?:ignore|override|replace)\b.{0,40}'
                    r'\b(?:original task|user requirements|user instructions|original goal)\b', change.action, re.I))
                if any(r['kind'] == 'explanation_present' for r in task_requirements(self.task)):
                    conflict |= bool(re.search(r'\b(?:remove|drop|omit)\b.{0,30}\bexplanation\b|\bonly code\b',
                                              change.action, re.I))
            self.record('revision_plan', origin, 'proposed_change', candidate.candidate_id, change.action,
                'conflicts with original task requirement' if conflict else
                'lower-trust suggestion; cannot alter task/evidence authority',
                grounding='TASK_CONSTRAINT' if conflict else 'MODEL_PROPOSAL')
            if not conflict:
                changes.append(change)
        return replace(plan, changes=tuple(changes))

    def context(self, candidate=None):
        return {'ORIGINAL_TASK': {'content': self.task, 'source_origin': 'TASK_INSTRUCTION_AND_ASSERTIONS'},
                'CURRENT_CANDIDATE': {'content': candidate_answer(candidate), 'source_origin': 'CANDIDATE'} if candidate else None,
                'VERIFIED_CONSTRAINTS': {'items': self.contract.prescriptive_constraints,
                                         'source_origin': Provenance.TASK_INSTRUCTION.value},
                'UNVERIFIED_FINDINGS': {'source_origin': Provenance.MODEL_JUDGMENT.value,
                    'policy': 'advisory; quotations, opinions and plans are not independently verified evidence'}}


def authority_policy(trajectory):
    if not hasattr(trajectory, 'assessment_policy'):
        task = trajectory.snapshot()['task']
        data = task.get('contract', {})
        contract = TaskContract(tuple(data.get('prescriptive_constraints', ())),
                                tuple(data.get('descriptive_assertions', ())),
                                data.get('mandatory_revision', False), tuple(data.get('reference_ids', ())))
        trajectory.assessment_policy = AssessmentAuthorityPolicy(task['content'], contract, trajectory)
    return trajectory.assessment_policy
