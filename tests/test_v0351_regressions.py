"""v0.3.5.1 S1–S17 and adversarial controls. Every provider is synthetic/offline."""
from dataclasses import replace
import json
from tempfile import TemporaryDirectory
import unittest

from end_engine import EndEngine, EngineConfig, TaskContract
from end_engine.core.state import Candidate, StopReason, VerificationResult
from end_engine.core.progress import InternalProgress, substantive_text
from end_engine.core.task_analyzer import TaskAnalyzer
from end_engine.core.weaknesses import WeaknessRegistry
from end_engine.cognition.session import CognitiveSession
from end_engine.experience import Trajectory
from end_engine.experience.serializer import dumps, loads
from end_engine.models.recording import RecordingProvider
from end_engine.quality.grounding import ground_issue
from end_engine.quality.epistemic import epistemic_integrity, extract_epistemic_claims
from end_engine.quality.integrity import content_sha256
from end_engine.quality.state import JudgeIssue, CheckContract, EvidenceArtifact
from end_engine.quality.mock import MockJudgeProvider, judgment_fixture
from end_engine.core.output_format import check_candidate, final_answer_region
from end_engine.cognition.state import Claim
from end_engine.verification import CallableToolVerifier, ToolCheck
from .test_v035_regressions import Gen, finding, adversary, objection

PROPERTY = 'Function raises ValueError for size zero.'
DEFECT = 'Function does not raise ValueError for size zero.'
GOOD = "```python\ndef validate(size):\n    if size <= 0:\n        raise ValueError('size')\n    return size\n```"
BAD = "```python\ndef validate(size):\n    return size\n```"


class Stagnant(Gen):
    def generate_structured(self, request):
        response = super().generate_structured(request)
        if request.purpose == 'verification':
            response = replace(response, content={**response.content, 'passed': False,
                               'remaining_issues': ['Model assessment remains inconclusive']})
        return response


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def engine(self, gen, **kwargs):
        config = kwargs.pop('config', EngineConfig(ledger_dir=self.temp.name, enable_branching=False))
        return EndEngine(config, provider=gen, **kwargs)

    def context(self, gen):
        engine = self.engine(gen)
        trajectory = Trajectory('Inspect bounded behavior', {}, {})
        registry = WeaknessRegistry()
        registry.ingest([finding()], 0)
        cognitive = CognitiveSession(TaskAnalyzer().analyze('Inspect bounded behavior', mode='normal'),
                                     engine.config, trajectory)
        return engine, trajectory, registry, cognitive, RecordingProvider(gen, trajectory, 1)

    def critique(self, gen, times=1):
        engine, trace, registry, cognitive, provider = self.context(gen)
        result = None
        for _ in range(times):
            result = engine._critique(next(iter(engine.operators.values())), provider, 'Inspect bounded behavior',
                Candidate('C0', None, 0, 'Candidate', ''), registry, None, cognitive, trace)
        return result, trace.snapshot(), gen


class SemanticTests(Fixture):
    @staticmethod
    def checker(task, candidate, tests, claims):
        assert candidate.content in (GOOD, BAD)
        namespace = {}
        exec(candidate.content.split('```python\n')[1].split('```')[0], namespace)
        try:
            namespace['validate'](0)
        except ValueError:
            passed = True
        else:
            passed = False
        return (ToolCheck(passed, PROPERTY, contract=CheckContract('zero-input', properties=(PROPERTY,),
            artifact_sha256=content_sha256(candidate.content), bounds='size zero')),)

    def semantic_run(self, content):
        judge = adversary(objection('The function fails to raise ValueError for size zero.',
            candidate_quote=content.split('```python\n')[1].split('```')[0].strip(),
            claim_type='CANDIDATE_INTERNAL', source_claim=PROPERTY, alleged_defect=DEFECT,
            basis='Behavior for size zero'))
        engine = self.engine(Gen(contents=[content]), judge_provider=judge,
                             tool_verifier=CallableToolVerifier(self.checker))
        result = engine.run('Fix validation for nonpositive size.', mode='normal', max_cycles=0)
        return result, engine.last_trajectory

    def test_S1_real_quote_wrong_behavior_is_contradicted_in_scope(self):
        _, record = self.semantic_run(GOOD)
        issue = record['adversarial_judgments'][0]['fatal_issues'][0]
        self.assertEqual((issue['textual_grounding'], issue['semantic_grounding'], issue['decisive']),
                         ('GROUNDED', 'SEMANTIC_CONTRADICTED', False))
        self.assertNotIn(record['quality_gate_decisions'][0]['decision'], ('REJECT', 'REVISE'))
        self.assertEqual(record['rollback_events'], [])
        self.assertEqual(record['judge_groundings'][0]['status'], 'SEMANTIC_CONTRADICTED')

    def test_S2_real_quote_legitimate_scoped_defect_stays_decisive(self):
        _, record = self.semantic_run(BAD)
        self.assertEqual(record['quality_gate_decisions'][0]['decision'], 'REJECT')
        self.assertEqual(record['fatal_issues'][0]['grounding'], 'SEMANTIC_SUPPORTED')

    def test_S3_quoted_factual_premise_cannot_decide_error(self):
        task = 'Library X guarantees exactly-once delivery. Explain its limits.'
        answer = 'Library X does not guarantee exactly-once delivery.'
        issue = JudgeIssue('correctness', 'The candidate contradicts the task premise that Library X guarantees delivery.',
                           candidate_quote=answer, task_reference='Library X guarantees exactly-once delivery.')
        grounded = ground_issue(issue, task, answer)
        self.assertEqual(grounded.textual, 'GROUNDED')
        self.assertEqual((grounded.status, grounded.decisive), ('TASK_PREMISE_DEPENDENT', False))

    def test_S4_explicit_hypothetical_remains_binding(self):
        task = 'For this hypothetical, assume the server is offline. Return a plan.'
        issue = JudgeIssue('constraint', 'Candidate ignores the prescribed assumption.', claim_type='TASK_CONSTRAINT',
                           task_reference='the server is offline', candidate_quote='The server is online.')
        self.assertTrue(ground_issue(issue, task, 'The server is online.').decisive)

    def test_task_contract_metadata_preserves_ambiguous_constraints(self):
        contract = TaskContract(prescriptive_constraints=('Server unavailable',))
        issue = JudgeIssue('constraint', 'Requires an unavailable server.', claim_type='TASK_CONSTRAINT',
                           task_reference='Server unavailable')
        self.assertTrue(ground_issue(issue, 'Plan work', 'Use server', contract=contract).decisive)

    def test_judge_cannot_label_descriptive_fact_as_constraint(self):
        issue = JudgeIssue('constraint', 'Wrong.', claim_type='TASK_CONSTRAINT', task_reference='Library X is safe')
        self.assertFalse(ground_issue(issue, 'Library X is safe.', 'Library X is unsafe.').decisive)

    def test_wrong_candidate_artifact_or_unrelated_check_cannot_override(self):
        issue = JudgeIssue('correctness', 'Wrong behavior', source_claim=PROPERTY, alleged_defect=DEFECT,
                           candidate_quote=GOOD)
        contract = CheckContract('scope', properties=(PROPERTY,), artifact_sha256=content_sha256(GOOD))
        evidence = EvidenceArtifact('E1', 'C9', 'EXECUTED_EVIDENCE', 'test', True, PROPERTY, contract=contract)
        for item in (evidence, replace(evidence, candidate_id='C0', contract=replace(contract, artifact_sha256='0'*64)),
                     replace(evidence, candidate_id='C0', contract=replace(contract, properties=('Unrelated behavior',)))):
            self.assertEqual(ground_issue(issue, 'Fix behavior', GOOD, evidence=(item,), candidate_id='C0').status,
                             'SEMANTIC_UNSUPPORTED')


class EpistemicTests(Fixture):
    def test_S5_unsupported_established_is_detected(self):
        self.assertTrue(epistemic_integrity('X is established.', 'C0')[0]['overclaim'])

    def test_S6_negative_polarity_is_allowed(self):
        for text in ('X is not established.', 'X cannot be confirmed.', 'The claim is not verified.',
                     'This does not prove X.', 'X is never independently confirmed.'):
            self.assertEqual(epistemic_integrity(text, 'C0'), (), text)
        self.assertEqual(check_candidate('Report status', 'C0',
            'Two engineers agree X, but this is not independently verified.')['consensus_as_confirmation'], [])

    def test_S7_human_model_and_decision_consensus_is_not_confirmation(self):
        for text in ('Two engineers independently confirmed X.', 'Generator, judge and Jev agree; X is verified.'):
            self.assertTrue(epistemic_integrity(text, 'C0')[0]['overclaim'])
        self.assertEqual(epistemic_integrity('Two engineers agree X, but this is not independently verified.', 'C0'), ())

    def test_S8_scoped_evidence_cannot_prove_universal_claim(self):
        text = 'X is verified under scenario A.'
        target = extract_epistemic_claims(text)[0].target
        claim = Claim('CL001', target, 'technical', 'C0')
        artifact = EvidenceArtifact('E1', 'C0', 'EXECUTED_EVIDENCE', 'trusted', True, 'Scoped check', ('CL001',),
            contract=CheckContract('check', claims=(target,), artifact_sha256=content_sha256(text), bounds='scenario A'))
        self.assertFalse(epistemic_integrity(text, 'C0', (claim,), (artifact,))[0]['overclaim'])
        self.assertTrue(epistemic_integrity('X is universally proven.', 'C0', (claim,), (artifact,))[0]['overclaim'])
        self.assertEqual(epistemic_integrity('X was observed under scenario A.', 'C0', (claim,), (artifact,)), ())

    def test_json_status_fields_and_nested_targets_are_detected(self):
        for key, value in [('certainty', 'established'), ('status', 'verified'), ('verification', 'confirmed'),
                           ('verified', True), ('confirmed', True), ('confidence', 1.0)]:
            text = json.dumps({'claim': 'X', key: value})
            self.assertTrue(epistemic_integrity(text, 'C0')[0]['overclaim'], key)
        text = json.dumps({'claim': 'X', 'verification': {'status': 'established'}})
        self.assertEqual(epistemic_integrity(text, 'C0')[0]['target'], 'X')

    def test_negated_json_status_and_mixed_polarity(self):
        self.assertEqual(epistemic_integrity('{"claim":"X","status":"not verified"}', 'C0'), ())
        checks = epistemic_integrity('X is not established, but Y is confirmed.', 'C0')
        self.assertEqual([c['declared_status'] for c in checks], ['confirmed'])

    def test_model_receipt_and_untargeted_pass_cannot_authorize(self):
        text = 'X is established.'
        claim = Claim('CL001', 'X', 'technical', 'C0')
        model = EvidenceArtifact('E1', 'C0', 'MODEL_JUDGMENT', 'model', True, 'Consensus', ('CL001',))
        untargeted = replace(model, evidence_type='EXECUTED_EVIDENCE', targets=(),
            contract=CheckContract('check', claims=('X',), artifact_sha256=content_sha256(text)))
        self.assertTrue(epistemic_integrity(text, 'C0', (claim,), (model, untargeted))[0]['overclaim'])

    def test_engine_requests_targeted_revision_then_withholds_unfixed_overclaim(self):
        answer = '```json\n{"claim":"X", "certainty":"established"}\n```'
        engine = self.engine(Gen(native=[answer]), config=EngineConfig(ledger_dir=self.temp.name,
            enable_branching=False, candidate_generation='native', quality_evaluation=True))
        result = engine.run('Return a JSON account of the available evidence.', mode='normal', max_cycles=1)
        record = engine.last_trajectory
        self.assertEqual(result.answer, '')
        self.assertEqual(result.quality_gate, 'BLOCKED')
        self.assertTrue(record['output_integrity']['blocked'])
        self.assertTrue(any(w['type'] == 'epistemic_output' for w in record['weaknesses']))
        revision = next(c['request'] for c in record['model_calls'] if c['request']['purpose'] == 'revision')
        self.assertIn('Preserve substantive possibilities', revision['prompt'])
        self.assertNotIn('W001', revision['prompt'])
        self.assertEqual(record['candidates'][0]['content'], answer)

    def test_safe_status_revision_wins_equal_gate_rank_without_verified_promotion(self):
        bad = '```json\n{"claim":"X", "certainty":"established"}\n```'
        safe = '```json\n{"claim":"X", "certainty":"unknown"}\n```'
        engine = self.engine(Stagnant(native=(bad, safe)), config=EngineConfig(ledger_dir=self.temp.name,
            enable_branching=False, candidate_generation='native', quality_evaluation=True))
        result = engine.run('Return evidence status as JSON.', mode='normal', max_cycles=1)
        self.assertEqual(result.answer, safe)
        self.assertEqual(result.quality_gate, 'BLOCKED')
        self.assertFalse(engine.last_trajectory['output_integrity']['blocked'])


class RepairTests(Fixture):
    def test_S9_repair_success_only_when_known_result_is_used(self):
        bad = {'summary': 's', 'findings': [finding('unknown')]}
        good = {'summary': 's', 'findings': [finding('W001')]}
        output, record, _ = self.critique(Gen(critiques=[bad, good]))
        self.assertEqual(output['findings'][0]['weakness_id'], 'W001')
        self.assertEqual(record['repair_statistics']['repair_succeeded'], 1)
        self.assertEqual(record['repair_statistics']['repair_failed'], 0)

    def test_S10_failed_repair_discards_without_external_failure(self):
        bad = {'summary': 's', 'findings': [finding('unknown')]}
        output, record, gen = self.critique(Gen(critiques=[bad, bad]))
        self.assertEqual(output['findings'], [])
        self.assertEqual((record['repair_statistics']['repair_failed'], gen.counts['critique']), (1, 2))
        self.assertEqual(record['repair_statistics']['invalid_elements_discarded'], 1)

    def test_S11_two_failed_repairs_suppress_later_attempt(self):
        bad = {'summary': 's', 'findings': [finding('unknown')]}
        _, record, gen = self.critique(Gen(critiques=[bad]*10), times=3)
        stats = record['repair_statistics']
        self.assertEqual((stats['repair_attempted'], stats['repair_failed'], stats['repair_suppressed']), (2, 2, 1))
        self.assertEqual(gen.counts['critique'], 5)
        self.assertEqual(stats['calls_saved_by_suppression'], 1)

    def test_S12_suppression_resets_with_each_trajectory(self):
        bad = {'summary': 's', 'findings': [finding('unknown')]}
        _, old, _ = self.critique(Gen(critiques=[bad]*10), times=3)
        _, fresh, _ = self.critique(Gen(critiques=[bad]*10))
        self.assertEqual(old['repair_statistics']['repair_suppressed'], 1)
        self.assertEqual(fresh['repair_statistics']['repair_suppressed'], 0)
        self.assertEqual(fresh['repair_statistics']['repair_attempted'], 1)

    def test_schema_repair_with_invalid_ids_is_not_counted_successful_or_repaired_again(self):
        from end_engine import ModelResponse
        bad = {'summary': 's', 'findings': [finding('unknown')]}
        output, record, gen = self.critique(Gen(critiques=[ModelResponse('not JSON'), bad]))
        self.assertEqual(gen.counts['critique'], 2)
        self.assertEqual(output['findings'], [])
        self.assertEqual(record['repair_statistics']['repair_succeeded'], 0)
        self.assertEqual(record['repair_statistics']['repair_failed'], 1)


class ProgressTests(Fixture):
    def stagnant_run(self, contents=('Alpha answer.',), contract=None, verifier=None):
        engine = self.engine(Stagnant(contents=contents), judge_provider=MockJudgeProvider(), verifier=verifier)
        result = engine.run('Inspect this bounded proposal.', mode='normal', max_cycles=5, task_contract=contract)
        return result, engine.last_trajectory

    def test_S13_two_stagnant_completed_cycles_stop(self):
        result, record = self.stagnant_run()
        self.assertEqual((result.termination_reason, result.iterations), (StopReason.NO_PROGRESS, 2))
        self.assertTrue(record['no_progress_stop'])

    def test_S14_punctuation_and_superficial_words_do_not_reset(self):
        result, record = self.stagnant_run(('Alpha answer.', 'The alpha answer!', 'Clearly alpha answer.'))
        self.assertEqual(result.termination_reason, StopReason.NO_PROGRESS)
        self.assertEqual(record['no_progress_cycles'], 2)
        self.assertNotEqual(substantive_text('X is safe'), substantive_text('X is not safe'))

    def test_S15_resolved_issue_resets_progress_counter(self):
        trace = Trajectory('Task', {}, {})
        progress = InternalProgress(trace)
        progress.observe(0, {'issue_state': ('open',)})
        progress.observe(1, {'issue_state': ('open',)})
        progress.observe(2, {'issue_state': ('resolved',)})
        self.assertEqual(progress.stagnant, 0)
        self.assertEqual(trace.snapshot()['cycle_progress'][-1]['reasons'], ['issue_state'])

    def test_substantive_candidate_change_resets_counter(self):
        result, record = self.stagnant_run(('Alpha answer.', 'Alpha answer.', 'Beta answer.'))
        self.assertEqual((result.termination_reason, result.iterations), (StopReason.NO_PROGRESS, 4))
        self.assertIn('candidate_content', record['cycle_progress'][1]['reasons'])

    def test_S16_mandatory_policy_and_deterministic_failure_override(self):
        result, record = self.stagnant_run(contract=TaskContract(mandatory_revision=True))
        self.assertEqual(result.termination_reason, StopReason.BUDGET_EXHAUSTED)
        self.assertFalse(record['no_progress_stop'])
        class Failed:
            def verify(self, *args):
                return VerificationResult(False, .2, (('correctness', .2),), ('Check failed',), (), 'basic_rules')
        result, record = self.stagnant_run(verifier=Failed())
        self.assertEqual(result.termination_reason, StopReason.BUDGET_EXHAUSTED)
        self.assertFalse(record['no_progress_stop'])

    def test_S17_no_progress_does_not_create_acceptance(self):
        result, record = self.stagnant_run(('X will hold.',))
        self.assertEqual(result.termination_reason, StopReason.NO_PROGRESS)
        self.assertEqual(result.quality_gate, 'BLOCKED')
        self.assertNotIn(result.acceptance_label, ('ACCEPTED_HIGH_CONFIDENCE', 'ACCEPTED_PROVISIONAL'))

    def test_additive_serialization_and_new_stop_round_trip(self):
        _, record = self.stagnant_run()
        self.assertEqual(loads(dumps(record)), record)
        self.assertEqual(record['schema_version'], '3.0')
        self.assertIn('repair_statistics', record)

    def test_repeated_rollback_to_same_candidate_is_not_progress(self):
        good = '```json\n{"value":1}\n```'
        bad = '```json\n{"value":2}\n```'
        def judge(request):
            if request.context['candidate']['content'] == good:
                return judgment_fixture(request.context['dimensions'])
            return judgment_fixture(request.context['dimensions'], verdict='FAIL', fatal=True, issues=[{
                'category': 'constraint', 'description': 'The required value is 1, but this outputs 2.',
                'target': 'value', 'fatal': True, 'evidence': [], 'claim_type': 'TASK_CONSTRAINT',
                'task_reference': 'value 1', 'candidate_quote': bad}])
        provider = MockJudgeProvider(scripted={'adversarial_judgment': [judge]*8})
        engine = self.engine(Stagnant(contents=(good, bad)), judge_provider=provider)
        result = engine.run('Return value 1 as a JSON object in a ```json code block.', mode='normal', max_cycles=5)
        record = engine.last_trajectory
        self.assertEqual(result.termination_reason, StopReason.NO_PROGRESS)
        self.assertEqual(result.answer, good)
        self.assertEqual(len(record['rollback_events']), 2)
        self.assertEqual(record['cycle_progress'][-1]['reasons'], [])

    def test_json_order_and_code_formatting_normalize_but_identifiers_do_not(self):
        self.assertEqual(substantive_text('```json\n{"b":2,"a":1}\n```'),
                         substantive_text('```json\n{"a":1, "b":2}\n```'))
        self.assertEqual(substantive_text('```python\nx = 1\n```'), substantive_text('```python\nx=1\n```'))
        self.assertNotEqual(substantive_text('```python\nx = 1\n```'), substantive_text('```python\nX=1\n```'))


class InspectionBudgetTests(unittest.TestCase):
    def test_valid_pre_final_draft_does_not_satisfy_final_output_format(self):
        raw = '```json\n{"draft":1}\n```\n</think>\nUnformatted final answer.'
        checked = check_candidate('Return a JSON object in a ```json code block.', 'C0', raw)
        self.assertEqual(len(checked['format_violations']), 2)

    def test_structured_status_enums_preserve_polarity_and_ceiling(self):
        self.assertTrue(epistemic_integrity('{"claim":"X","status":"VERIFIED_WITHIN_SCOPE"}', 'C0')[0]['overclaim'])
        self.assertEqual(epistemic_integrity('{"claim":"X","status":"NOT_VERIFIED"}', 'C0'), ())
        self.assertEqual(epistemic_integrity('{"claim":"X","status":"UNVERIFIED"}', 'C0'), ())

    def test_ignored_deliberation_is_not_returned_and_literal_markers_are_preserved(self):
        raw = 'X is established.\n</think>\nX is not established.'
        self.assertEqual(final_answer_region(raw), 'X is not established.')
        self.assertEqual(epistemic_integrity(raw, 'C0'), ())
        literal = '```text\n</think>\n```'
        self.assertEqual(final_answer_region(literal), literal)
        self.assertEqual(final_answer_region('Inline </think> example'), 'Inline </think> example')

    def test_conflicting_checks_never_establish_status_or_choose_a_side_by_order(self):
        text = 'X is verified under scenario A.'
        target = extract_epistemic_claims(text)[0].target
        claim = Claim('CL001', target, 'technical', 'C0')
        artifact = EvidenceArtifact('E1', 'C0', 'EXECUTED_EVIDENCE', 'trusted', True, 'Check', ('CL001',),
            contract=CheckContract('test', claims=(target,), artifact_sha256=content_sha256(text), bounds='scenario A'))
        failed = replace(artifact, artifact_id='E2', passed=False)
        for evidence in ((artifact, failed), (failed, artifact)):
            result = epistemic_integrity(text, 'C0', (claim,), evidence)[0]
            self.assertTrue(result['overclaim'])
            self.assertEqual(result['supported_status'], 'UNVERIFIED')
        issue = JudgeIssue('correctness', 'Runtime behavior', candidate_quote=GOOD,
                           source_claim=PROPERTY, alleged_defect=DEFECT)
        contract = CheckContract('zero', properties=(PROPERTY,), artifact_sha256=content_sha256(GOOD))
        checked = replace(artifact, contract=contract)
        failed = replace(checked, artifact_id='E2', passed=False)
        for evidence in ((checked, failed), (failed, checked)):
            self.assertEqual(ground_issue(issue, 'Check behavior', GOOD, evidence=evidence, candidate_id='C0').status,
                             'SEMANTIC_UNSUPPORTED')

    def test_large_output_and_deep_json_cannot_bypass_the_bounded_guard(self):
        self.assertTrue(epistemic_integrity('x'*32001, 'C0')[-1]['overclaim'])
        value = {'claim': 'X', 'verified': True}
        for _ in range(7):
            value = {'nested': value}
        self.assertTrue(epistemic_integrity(json.dumps(value), 'C0')[-1]['overclaim'])

    def test_not_only_is_affirmative_and_personal_execution_claim_is_bound(self):
        self.assertTrue(epistemic_integrity('X is not only verified.', 'C0')[0]['overclaim'])
        self.assertEqual(extract_epistemic_claims('I verified X.')[0].target, 'X')


if __name__ == '__main__':
    unittest.main()
