"""Deterministic v0.3.5.2 integrity controls; no live provider or benchmark execution."""
from dataclasses import replace
import json
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, TaskContract
from end_engine.core.state import Candidate, Change, RevisionPlan, VerificationResult, WeaknessStatus
from end_engine.core.output_format import extract_answer_region, candidate_answer, check_candidate
from end_engine.core.task_contract import assertion_kind
from end_engine.core.progress import InternalProgress, progress_state
from end_engine.core.weaknesses import WeaknessRegistry
from end_engine.experience.schema import Trajectory
from end_engine.experience.serializer import dumps, loads
from end_engine.quality.assessment import AssessmentAuthorityPolicy
from end_engine.quality.epistemic import extract_epistemic_claims, epistemic_integrity
from end_engine.quality.grounding import ground_issue
from end_engine.quality.revision_integrity import evidence_delta, evidence_violations
from end_engine.quality.integrity import content_sha256
from end_engine.quality.state import JudgeIssue, CheckContract, EvidenceArtifact
from end_engine.cognition.state import Claim
from end_engine.cognition.session import CognitiveSession
from end_engine.core.task_analyzer import TaskAnalyzer
from end_engine.models import MockProvider, ModelResponse
from end_engine.quality.mock import MockJudgeProvider


def candidate(text, identity='C0', parent=None):
    return Candidate(identity, parent, int(identity[1:]), text, '')


def finding(description, evidence=''):
    return {'weakness_id': None, 'type': 'correctness', 'severity': 'high',
            'description': description, 'evidence': evidence}


def receipt(c, text, passed=True, bounds='scope A'):
    return EvidenceArtifact('R1', c.candidate_id, 'EXECUTED_EVIDENCE', 'trusted:check', passed,
        'Bounded executed check', ('CL001',), contract=CheckContract('T', claims=(text,),
        properties=(text,), artifact_sha256=content_sha256(c.content), bounds=bounds))


TASK = 'Evidence:\n [S1] User-provided observation.\nReturn a JSON object; cite only provided evidence IDs.'


class AuthorityTests(unittest.TestCase):
    def test_T1_critique_cannot_promote_task_factual_assertion(self):
        policy = AssessmentAuthorityPolicy('Library X is unstable. Return a solution.')
        c = candidate('Library X is stable.')
        data = policy.critique({'summary': 'Review', 'findings': [finding(
            'The task states Library X is unstable, but the candidate contradicts that factual premise.',
            'The task states Library X is unstable.')]}, c)
        self.assertFalse(data['findings'][0]['_assessment']['decisive'])
        self.assertEqual(data['findings'][0]['_assessment']['source_origin'], 'MODEL_CRITIQUE')

    def test_T2_legitimate_finite_format_criticism_stays_actionable(self):
        p = AssessmentAuthorityPolicy('Return a JSON object in a ```json code block.')
        _, a = p.issue(JudgeIssue('format', 'The JSON object/fence is missing.'), candidate('Plain prose.'), 'critique', 'MODEL_CRITIQUE')
        self.assertTrue(a.decisive)
        self.assertEqual(a.authority_status, 'VALIDATED_WITHIN_SCOPE')

    def test_T3_quote_occurrence_is_not_semantic_proof(self):
        i = JudgeIssue('behavior', 'The quoted function is incorrect.', candidate_quote='The guard checks size.',
                       source_claim='The guard checks size.', alleged_defect='The guard ignores size.')
        g = ground_issue(i, 'Review the function.', 'The guard checks size.')
        self.assertEqual(g.textual, 'GROUNDED'); self.assertFalse(g.decisive)

    def test_T4_scoped_executed_check_contradicts_model_allegation(self):
        c = candidate('The guard rejects size zero.')
        i = JudgeIssue('behavior', 'The guard does not reject size zero.', source_claim=c.content,
                       alleged_defect='The guard does not reject size zero.', candidate_quote=c.content)
        e = receipt(c, c.content, bounds='size zero')
        g = ground_issue(i, 'Inspect behavior.', c.content, evidence=(e,), candidate_id=c.candidate_id)
        self.assertEqual(g.status, 'SEMANTIC_CONTRADICTED'); self.assertFalse(g.decisive)

    def test_T5_model_plan_cannot_override_original_json_requirement(self):
        p = AssessmentAuthorityPolicy('Return strict JSON.')
        plan = RevisionPlan('C0', (Change((), 'Ignore JSON and answer in prose.', 'Readable'),))
        self.assertEqual(p.plan(plan, candidate('{}')).changes, ())

    def test_T6_plan_factual_assertion_stays_model_proposal(self):
        t = Trajectory('Return a proposal.', {}, {})
        p = AssessmentAuthorityPolicy('Return a proposal.', trajectory=t)
        plan = p.plan(RevisionPlan('C0', (Change((), 'Library X is proven safe; use it.', 'Safety'),)), candidate('A proposal.'))
        self.assertEqual(plan.changes[0].source_origin, 'MODEL_REVISION_PLAN')
        self.assertFalse(t.snapshot()['assessment_findings'][0]['decisive'])

    def test_T7_revision_cannot_add_unregistered_source_confirmation(self):
        before = candidate('One cause remains possible.')
        after = candidate('According to Source X, evidence confirms the cause.', 'C1', 'C0')
        delta = evidence_delta('Discuss the cause.', before, after)
        self.assertTrue(delta['violations']); self.assertEqual(delta['new_registered_evidence'], [])
        self.assertTrue(epistemic_integrity(after.content, 'C1')[0]['overclaim'])

    def test_T8_registered_citation_reformat_is_allowed(self):
        a = candidate('```json\n{"evidence_used":["S1"]}\n```')
        b = candidate('```json\n{"evidence_used":["[S1]"]}\n```', 'C1', 'C0')
        self.assertEqual(evidence_delta(TASK, a, b)['violations'], ())

    def test_T9_safe_uncertainty_revision_needs_no_invented_evidence(self):
        c = candidate('A fault remains one possibility; independent confirmation is unavailable.')
        self.assertEqual(extract_epistemic_claims(c.content), ())
        self.assertEqual(evidence_violations('Discuss causes.', c), ())

    def test_T10_evidence_confirms_is_checked(self):
        for text in ('Evidence confirms X.', 'The evidence used confirms X, but quantitative details are absent.',
                     'This test confirms X.'):
            with self.subTest(text=text):
                self.assertTrue(any(x['overclaim'] for x in epistemic_integrity(text, 'C0')))

    def test_T11_negative_confirmation_is_not_blocked(self):
        for text in ('There is no evidence confirming X.', 'No evidence confirms X.', 'X is not verified.'):
            self.assertEqual(extract_epistemic_claims(text), (), text)

    def test_T12_user_attribution_and_hypothesis_are_not_endorsement(self):
        for text in ('The user claims the report confirms X.', 'If the report confirmed X, we could conclude Y.',
                     '"Evidence confirms X."', 'Hypothetically, evidence confirms X.'):
            self.assertEqual(extract_epistemic_claims(text), (), text)

    def test_T13_narrow_receipt_cannot_authorize_universal_verification(self):
        c = candidate('Evidence proves scope A always holds without exception.')
        claim = Claim('CL001', 'scope A always holds without exception', 'technical', 'C0')
        self.assertTrue(epistemic_integrity(c.content, 'C0', (claim,), (receipt(c, 'scope A'),))[0]['overclaim'])

    def test_T14_exact_scoped_statement_with_receipt_is_allowed(self):
        c = candidate('Evidence confirms scope A.')
        claim = Claim('CL001', 'scope A', 'technical', 'C0')
        self.assertFalse(epistemic_integrity(c.content, 'C0', (claim,), (receipt(c, 'scope A'),))[0]['overclaim'])

    def test_T15_wrappers_ignore_incidental_inline_backticks(self):
        raw = 'Thinking mentions ```json as an example.\n</think>\n```json\n{}\n```'
        r = extract_answer_region(raw)
        self.assertEqual(r.status, 'WRAPPER_BOUNDARY'); self.assertEqual(r.content, '```json\n{}\n```')
        c = replace(candidate(raw), answer_content=r.content, answer_region_status=r.status)
        self.assertEqual(check_candidate('Return a JSON object.', 'C0', candidate_answer(c))['format_violations'], [])

    def test_T16_ambiguous_extraction_cannot_be_accepted_silently(self):
        raw = 'Reasoning\n</think>\nAnswer one\n</think>\nAnswer two'
        self.assertEqual(extract_answer_region(raw).status, 'AMBIGUOUS')
        with TemporaryDirectory() as path:
            gen = MockProvider(scripted={'initial_candidate': [{'content':raw,'known_strengths':[],'confidence':None}]})
            e = EndEngine(EngineConfig(ledger_dir=path), provider=gen)
            result = e.run('Return an answer.', mode='fast', max_cycles=0)
            self.assertEqual(result.answer, '')
            self.assertTrue(e.last_trajectory['output_integrity']['answer_region_ambiguous'])

    def test_T17_unknown_citation_id_is_a_deterministic_reference_violation(self):
        c = candidate('```json\n{"evidence_used":["S999"]}\n```')
        violations = evidence_violations(TASK, c)
        self.assertEqual(violations[0]['reference'], 'S999')
        self.assertIn('no claim that the external source', violations[0]['scope'])
        _, f = AssessmentAuthorityPolicy(TASK).issue(JudgeIssue('citation', 'S999 is outside the declared references.'), c)
        self.assertTrue(f.decisive)

    def test_T18_registered_source_newly_referenced_is_not_false_rejected(self):
        c = candidate('```json\n{"evidence_used":["R1"]}\n```')
        self.assertEqual(evidence_violations(TASK, c, (receipt(c, 'A property'),)), ())

    def state(self, registry=None):
        t = Trajectory('Inspect a proposal.', {}, {})
        config = EngineConfig()
        cognitive = CognitiveSession(TaskAnalyzer().analyze('Inspect a proposal.', mode='normal'), config, t)
        return t, cognitive, registry or WeaknessRegistry()

    def test_T19_unsupported_model_issue_creation_is_not_substantive_progress(self):
        t, cognitive, registry = self.state(); c = candidate('Same answer.')
        before = progress_state(c, registry, cognitive, None)
        p = AssessmentAuthorityPolicy('Inspect a proposal.')
        output = p.critique({'summary':'Review','findings':[finding('An unexplained imaginary defect.')]}, c)
        registry.ingest(output['findings'], 1)
        after = progress_state(c, registry, cognitive, None)
        self.assertEqual(before, after)
        self.assertEqual(len(registry.snapshot()), 1)  # retained, not erased

    def test_T20_grounded_issue_resolution_changes_progress(self):
        t, cognitive, registry = self.state(); c = candidate('Same answer.')
        registry.ingest([{**finding('Missing JSON.'),'_assessment':{
            'source_origin':'ENGINE_DERIVED','authority_status':'VALIDATED_WITHIN_SCOPE','decisive':True}}], 0)
        before = progress_state(c, registry, cognitive, None)
        from end_engine.core.state import WeaknessUpdate
        registry.apply_updates((WeaknessUpdate('W001', WeaknessStatus.RESOLVED, 'Finite check passes now.'),))
        self.assertNotEqual(before, progress_state(c, registry, cognitive, None))

    def test_T21_identical_effective_state_after_rollback_is_stagnant(self):
        t, cognitive, registry = self.state(); c = candidate('Original answer.')
        p = InternalProgress(t, 2); state = progress_state(c, registry, cognitive, None)
        p.observe(0, state); self.assertFalse(p.observe(1, state)); self.assertTrue(p.observe(2, state))

    def test_T22_mandatory_actions_and_contradictions_block_no_progress_shortcut(self):
        for blocker in ('mandatory revision remains', 'unresolved deterministic verification failure',
                        'protocol recovery pending', 'mandatory deterministic output-format revision'):
            t, cognitive, registry = self.state(); p = InternalProgress(t, 2)
            state = progress_state(candidate('Same answer.'), registry, cognitive, None)
            p.observe(0, state); p.observe(1, state, (blocker,))
            self.assertFalse(p.observe(2, state, (blocker,)))
            self.assertNotIn('acceptance_label', t.snapshot()['cycle_progress'][-1])

    def test_T23_model_and_offline_decision_agreement_is_not_verification(self):
        c = candidate('Evidence confirms scope A.'); claim = Claim('CL001','scope A','technical','C0')
        e = replace(receipt(c, 'scope A'), evidence_type='MODEL_JUDGMENT')
        self.assertTrue(epistemic_integrity(c.content, 'C0', (claim,), (e,))[0]['overclaim'])
        from end_engine.decisions.providers import DeterministicDecisionProvider
        from end_engine.decisions.types import DecisionRequest
        decision = DeterministicDecisionProvider().evaluate(DecisionRequest('D1','choice','Choose agreement.',
            '{"family_utility":{"agree":1}}', ('agree','other')))
        self.assertEqual(decision.value.selected_choice, 'agree')
        self.assertEqual(decision.provenance.evidence_type, 'MODEL_JUDGMENT')
        self.assertTrue(epistemic_integrity(c.content, 'C0', (claim,), (e,))[0]['overclaim'])

    def test_T24_legacy_schema_records_still_load_without_mutation(self):
        from pathlib import Path
        p = next(Path('v035_core_regression_pilot/trajectories').glob('*.jsonl'))
        raw = p.read_text(encoding='utf-8'); data = loads(raw)
        self.assertEqual(json.loads(raw), data); self.assertEqual(loads(dumps(data)), data)

    def test_adapter_boundary_is_preserved_in_recorded_response_and_candidate(self):
        raw = 'Reasoning\n</think>\nLiteral answer\n</think>\nextra'
        region = extract_answer_region(raw, 'Literal answer')
        self.assertEqual(region.status, 'ADAPTER_BOUNDARY')
        with TemporaryDirectory() as path:
            gen = MockProvider(scripted={'initial_candidate':[ModelResponse({'content':raw,'known_strengths':[],
                'confidence':None}, answer_content='Literal answer')]})
            e = EndEngine(EngineConfig(ledger_dir=path), provider=gen)
            self.assertEqual(e.run('Return an answer.',mode='fast',max_cycles=0).answer, 'Literal answer')

    def test_literal_marker_inside_real_code_fence_is_not_a_wrapper(self):
        text = '```python\n</think>\n```'
        self.assertEqual(extract_answer_region(text).content, text)

    def test_possible_external_source_discussion_is_allowed(self):
        c = candidate('If Source X becomes available, it could confirm the hypothesis.')
        self.assertEqual(evidence_violations('Discuss possible sources.', c), ())

    def test_verifier_unknown_allegation_has_no_defect_authority(self):
        t, cognitive, registry = self.state()
        raw = VerificationResult(False, .2, (('correctness',.2),), ('The code is wrong.',), verifier='llm')
        result = AssessmentAuthorityPolicy('Review the code.').verification(raw,candidate('A program.'),registry)
        self.assertFalse(result.assessment_decisive); self.assertTrue(result.assessment_requires_evidence)
        self.assertFalse(result.passed); self.assertEqual(result.advisory_issues, raw.remaining_issues)

    def test_multiple_task_sentences_preserve_prescriptive_classification(self):
        task = 'Return JSON. Produce exactly three entries.'
        self.assertEqual(assertion_kind(task, task), 'PRESCRIPTIVE_TASK_CONSTRAINT')
        self.assertEqual(assertion_kind('Library X is unstable. Return JSON.',
                        'Library X is unstable. Return JSON.'), 'AMBIGUOUS_TASK_PROVIDED')

    def test_entry_count_constraint_and_valid_nested_entries(self):
        task = 'Return a JSON array with exactly three entries.'
        self.assertFalse(check_candidate(task,'C0','[{"n":1},{"n":2},{"n":3}]')['format_violations'])
        self.assertTrue(check_candidate(task,'C0','[1,2]')['format_violations'])

    def test_strict_json_and_valid_model_guided_revision(self):
        task = 'Return strict JSON.'
        self.assertFalse(check_candidate(task,'C0','{"n":1}')['format_violations'])
        self.assertTrue(check_candidate(task,'C0','Prose {"n":1}')['format_violations'])
        plan = RevisionPlan('C0',(Change((), 'Clarify the JSON value while retaining its shape.', 'Clarity'),))
        self.assertEqual(AssessmentAuthorityPolicy(task).plan(plan,candidate('{}')),plan)

    def test_valid_hypothetical_state_is_not_false_rejected(self):
        task = 'For this hypothetical, assume the server is offline. Return a plan.'
        i = JudgeIssue('constraint','Wrong server state.',claim_type='TASK_CONSTRAINT',
                       task_reference='the server is offline',candidate_quote='The server is offline.')
        self.assertFalse(ground_issue(i,task,'The server is offline. The client is online.').decisive)

    def test_missing_execution_receipt_is_detected_and_matching_scope_allowed(self):
        c = candidate('Check T passed scope A.')
        self.assertTrue(epistemic_integrity(c.content,'C0')[0]['overclaim'])
        claim = Claim('CL001', c.content.rstrip('.'), 'technical','C0')
        e = receipt(c,claim.text)
        self.assertFalse(epistemic_integrity(c.content,'C0',(claim,),(e,))[0]['overclaim'])

    def test_unknown_citation_is_withheld_in_full_engine(self):
        text = '```json\n{"evidence_used":["S999"],"certainty":"unknown"}\n```'
        with TemporaryDirectory() as path:
            gen = MockProvider(scripted={'initial_candidate':[{'content':text,'known_strengths':[],'confidence':None}]})
            e = EndEngine(EngineConfig(ledger_dir=path,quality_evaluation=True),provider=gen)
            result = e.run(TASK,mode='normal',max_cycles=0)
            self.assertEqual(result.answer,'');self.assertEqual(result.quality_gate,'BLOCKED')
            self.assertTrue(e.last_trajectory['revision_evidence_deltas'][0]['violations'])

    def test_requested_explanation_cannot_disappear_from_a_revision(self):
        task = 'Return a Python function and briefly explain its behavior.'
        good = '```python\ndef f(): return 1\n```\nThe function returns one.'
        bad = '```python\ndef f(): return 1\n```'
        self.assertFalse(check_candidate(task,'C0',good)['format_violations'])
        self.assertTrue(check_candidate(task,'C1',bad)['format_violations'])
        p = AssessmentAuthorityPolicy(task)
        self.assertEqual(p.plan(RevisionPlan('C0',(Change((), 'Drop the explanation.', 'Shorter'),)),candidate(good)).changes,())

    def test_external_library_constraint_and_stdlib_negative_control(self):
        task = 'Return Python code. Do not use external libraries.'
        self.assertFalse(check_candidate(task,'C0','```python\nimport json\n```')['format_violations'])
        self.assertTrue(check_candidate(task,'C1','```python\nimport requests\n```')['format_violations'])

    def test_descriptive_format_assertion_does_not_create_an_instruction(self):
        task = 'Library X returns a JSON object. Explain its limitations.'
        self.assertFalse(check_candidate(task,'C0','There are important limitations.')['format_violations'])

    def test_scoped_checker_and_judges_receive_the_actual_native_answer(self):
        from end_engine.verification import CallableToolVerifier, ToolCheck
        raw = 'Internal text claims everything is verified.\n</think>\nEvidence confirms scope A.'
        seen = []
        def checker(task,c,tests,claims):
            seen.append(c.content)
            return (ToolCheck(True,'Scoped A check', tuple(x.claim_id for x in claims),
                contract=CheckContract('A',claims=('scope A',),artifact_sha256=content_sha256(c.content),bounds='scope A')),)
        with TemporaryDirectory() as path:
            gen = MockProvider(scripted={'initial_candidate':[{'content':raw,'known_strengths':[],'confidence':None}]})
            e=EndEngine(EngineConfig(ledger_dir=path,quality_evaluation=True),provider=gen,
                        tool_verifier=CallableToolVerifier(checker))
            result=e.run('Return an answer.',mode='normal',max_cycles=0)
            self.assertEqual(seen,['Evidence confirms scope A.'])
            self.assertEqual(result.answer,'Evidence confirms scope A.')
            self.assertEqual(e.last_trajectory['candidates'][0]['content'],raw)
            judge=[c for c in e.last_trajectory['model_calls'] if c['request']['purpose']=='judgment'][0]
            self.assertEqual(judge['request']['context']['candidate']['content'],result.answer)

    def test_scoped_pass_overrides_the_same_literal_negative_in_verification(self):
        from end_engine.verification import CallableToolVerifier, ToolCheck
        text='The guard rejects size zero.'
        def verifier(request):
            return {'passed':False,'score':.4,'dimensions':{d:.4 for d in request.context['dimensions']},
                    'remaining_issues':['The guard does not reject size zero.'],'weakness_updates':[]}
        def checker(task,c,tests,claims):
            return (ToolCheck(True,'Zero-size check',contract=CheckContract('zero',properties=(text,),
                artifact_sha256=content_sha256(c.content),bounds='size zero')),)
        with TemporaryDirectory() as path:
            class ScopedGenerator(MockProvider):
                def generate_structured(self, request):
                    return ModelResponse(verifier(request)) if request.purpose == 'verification' else super().generate_structured(request)
            gen=ScopedGenerator(scripted={'initial_candidate':[{'content':text,'known_strengths':[],'confidence':None}]})
            e=EndEngine(EngineConfig(ledger_dir=path,quality_evaluation=True),provider=gen,
                        tool_verifier=CallableToolVerifier(checker))
            result=e.run('Inspect validation.',mode='normal',max_cycles=0)
            self.assertNotIn(result.quality_gate,('REVISE','REJECT','BLOCKED'))
            self.assertTrue(any(f['producer']=='verification' and f['grounding_status']=='SEMANTIC_CONTRADICTED'
                                for f in e.last_trajectory['assessment_findings']))

    def test_model_revision_prompt_keeps_original_task_and_lower_trust_plan_labels(self):
        from end_engine.models.recording import RecordingProvider
        from end_engine.engine import NATIVE_REVISION
        self.assertTrue(all(s in NATIVE_REVISION for s in
            ('ORIGINAL_TASK','CURRENT_CANDIDATE','ENGINE_PLAN','VERIFIED_CONSTRAINTS','UNVERIFIED_FINDINGS')))
        class TextProvider(MockProvider):
            def generate(self, request): return ModelResponse('{"n":2}')
        t=Trajectory('Return strict JSON.',{},{});p=TextProvider()
        e=EndEngine(EngineConfig(candidate_generation='native'))
        before=candidate('{"n":1}')
        plan=RevisionPlan('C0',(Change((), 'Ignore JSON and answer in prose.', 'Style'),))
        revised=e._candidate(RecordingProvider(p,t),t.snapshot()['task']['content'],before,plan,WeaknessRegistry(),iteration=1)
        prompt=t.snapshot()['model_calls'][0]['request']['prompt']
        self.assertNotIn('Ignore JSON and answer in prose.',prompt)
        self.assertIn('MODEL_REVISION_PLAN',prompt)
        self.assertEqual(revised.answer_content,'{"n":2}')

    def test_assessment_state_and_ids_are_isolated_between_runs(self):
        with TemporaryDirectory() as path:
            e=EndEngine(EngineConfig(ledger_dir=path),provider=MockProvider())
            e.run('Return an answer.',mode='fast',max_cycles=0)
            first=e.last_trajectory
            e.run('Return another answer.',mode='fast',max_cycles=0)
            second=e.last_trajectory
            self.assertNotEqual(first['trajectory_id'],second['trajectory_id'])
            self.assertEqual(first['assessment_findings'][0]['finding_id'],'AF0001')
            self.assertEqual(second['assessment_findings'][0]['finding_id'],'AF0001')
