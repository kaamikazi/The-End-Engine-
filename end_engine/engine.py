from dataclasses import replace
import logging
import traceback
from time import perf_counter

from .config import EngineConfig
from .core.question_selector import AdaptiveQuestionSelector, LLMQuestionSelector, SelectionContext
from .core.revision_planner import RevisionPlanner
from .core.state import (Candidate, Complexity, Critique, EngineResult, StopReason,
                         VerificationResult, now, to_data)
from .core.task_analyzer import TaskAnalyzer
from .core.termination import TerminationController
from .core.weaknesses import WeaknessRegistry
from .experience import JsonLedger, Trajectory
from .experience.serializer import dumps
from .models import MockProvider, ModelRequest
from .models.recording import RecordingProvider
from .models.schema import CANDIDATE, validate, verification_schema
from .operators import default_operators
from .verification import LLMVerifier
from .cognition.branches import BranchController
from .cognition.policy import UtilitySelectionPolicy
from .cognition.questions import QuestionGenerator
from .cognition.session import CognitiveSession, MetaController
from .cognition.state import TargetType
from .quality.session import QualitySession
from .quality.mock import MockJudgeProvider
from .quality.state import GateDecision


logger = logging.getLogger("end_engine")


class EndEngine:
    def __init__(self, config=None, *, provider=None, analyzer=None, selector=None,
                 planner=None, verifier=None, termination=None, ledger=None, operators=None,
                 selection_policy=None, question_generator=None, claim_extractor=None,
                 deduplicator=None, branch_evaluator=None, synthesis_planner=None, meta_controller=None,
                 judge_provider=None, secondary_judge_provider=None, adversarial_judge_provider=None, tool_verifier=None):
        self.config = config if config is not None else EngineConfig()
        self.provider = provider if provider is not None else MockProvider()
        self.analyzer = analyzer if analyzer is not None else TaskAnalyzer()
        self.selector = selector if selector is not None else (
            LLMQuestionSelector() if self.config.llm_selection else AdaptiveQuestionSelector())
        self.planner = planner if planner is not None else RevisionPlanner()
        self.verifier = verifier
        self.termination = termination if termination is not None else TerminationController(self.config)
        self.ledger = ledger if ledger is not None else JsonLedger(self.config.ledger_dir)
        self.operators = dict(operators if operators is not None else default_operators())
        if not self.operators or any(name != op.name for name, op in self.operators.items()):
            raise ValueError("Operators must be a nonempty mapping keyed by operator name")
        self._last_trajectory = None
        self.selection_policy = selection_policy
        self.question_generator = question_generator if question_generator is not None else QuestionGenerator()
        self.claim_extractor = claim_extractor
        self.deduplicator = deduplicator
        self.branch_evaluator = branch_evaluator
        self.synthesis_planner = synthesis_planner
        self.meta_controller = meta_controller if meta_controller is not None else MetaController()
        self.judge_provider = judge_provider
        self.secondary_judge_provider = secondary_judge_provider
        self.adversarial_judge_provider = adversarial_judge_provider
        self.tool_verifier = tool_verifier

    @property
    def last_trajectory(self):
        return self._last_trajectory.snapshot() if self._last_trajectory is not None else None

    def _log(self, message):
        if self.config.verbose:
            logger.info("[END] %s", message)

    def run(self, task, *, mode=None, max_cycles=None):
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task must be a nonempty string")
        if mode is not None:
            Complexity(mode)
        if max_cycles is not None and (type(max_cycles) is not int or max_cycles < 0):
            raise ValueError("max_cycles must be a nonnegative integer")
        start = perf_counter()
        configuration = {**to_data(self.config), "overrides": {"mode": mode, "max_cycles": max_cycles},
                         "components": {"analyzer": type(self.analyzer).__name__, "selector": type(self.selector).__name__,
                                        "planner": type(self.planner).__name__,
                                        "verifier": type(self.verifier).__name__ if self.verifier else "LLMVerifier",
                                        "termination": type(self.termination).__name__, "ledger": type(self.ledger).__name__,
                                        "selection_policy": type(self.selection_policy).__name__ if self.selection_policy else "UtilitySelectionPolicy",
                                        "branch_evaluator": type(self.branch_evaluator).__name__ if self.branch_evaluator else "LLMBranchEvaluator",
                                        "synthesis_planner": type(self.synthesis_planner).__name__ if self.synthesis_planner else "SynthesisPlanner",
                                        "question_generator": type(self.question_generator).__name__,
                                        "claim_extractor": type(self.claim_extractor).__name__ if self.claim_extractor else "ClaimExtractor",
                                        "deduplicator": type(self.deduplicator).__name__ if self.deduplicator else "TokenFindingDeduplicator",
                                        "meta_controller": type(self.meta_controller).__name__},
                         "operators": [to_data(op) for op in self.operators.values()]}
        trajectory = Trajectory(task, configuration, {"provider": "unknown"})
        quality_enabled = self.config.quality_evaluation or self.judge_provider is not None
        if quality_enabled:
            trajectory.set("schema_version", "3.0")
        self._last_trajectory = trajectory
        provider = RecordingProvider(self.provider, trajectory)
        verifier = self.verifier if self.verifier is not None else LLMVerifier(provider)
        if isinstance(verifier, LLMVerifier):
            judge_provider = verifier.provider
            recorded_judge = provider if judge_provider is None or judge_provider is provider or judge_provider is self.provider else RecordingProvider(judge_provider, trajectory)
            verifier = LLMVerifier(recorded_judge)
        registry = WeaknessRegistry(self.deduplicator)
        cognitive, branch_controller, quality = None, None, None
        accepted_at = None
        candidates, critiques, used, scores = [], [], [], []
        verification = None
        iterations, repeats = 0, 0
        previous_fingerprint = None
        stage = "provider_metadata"
        reason, explanation = StopReason.EXTERNAL_BLOCKER, "Execution did not complete"
        try:
            metadata = self.provider.metadata()
            dumps(metadata)
            trajectory.set("model", metadata)
            stage = "task_analysis"
            analysis = self.analyzer.analyze(task, provider, use_llm=self.config.llm_classification,
                                             mode=mode, max_cycles=max_cycles)
            trajectory.set("analysis", analysis)
            trajectory.record("task_analysis", analysis)
            cognitive = CognitiveSession(analysis, self.config, trajectory, self.claim_extractor)
            branch_controller = BranchController(self.config, trajectory, cognitive,
                evaluator=self.branch_evaluator, synthesis=self.synthesis_planner)
            if quality_enabled:
                stage = "quality_setup"
                quality = QualitySession(self.config, trajectory, metadata, self.judge_provider or MockJudgeProvider(),
                    self.secondary_judge_provider, self.adversarial_judge_provider, self.tool_verifier)
            self._log(f"Task classified: {analysis.complexity.value.upper()}")
            stage = "initial_candidate"
            current = self._candidate(provider, task, None, None, registry)
            candidates.append(current)
            trajectory.record("candidate", current, "candidates")
            if analysis.complexity is not Complexity.FAST:
                cognitive.knowledge.observe_candidate(current)
            self._log(f"Candidate {current.candidate_id} generated")
            stage = "verification"
            verification = self._verify(verifier, task, current, trajectory, registry)
            scores.append(verification.score)
            while True:
                gate = None
                if quality is not None:
                    stage = "quality_evaluation"
                    parent = next((c for c in candidates if c.candidate_id == current.parent_candidate_id), None)
                    evaluated, rollback = quality.evaluate(task, current, parent, verification, cognitive, registry,
                                                           branch_controller.snapshot(), scores)
                    self._log(f"[JUDGE] {evaluated.judgments[0].verdict.value}; [QUALITY] {evaluated.gate.decision.value}")
                    if rollback:
                        self._log(f"[ROLLBACK] {current.candidate_id} -> {rollback}")
                        current = next(c for c in candidates if c.candidate_id == rollback)
                        quality.restore(rollback, cognitive, registry)
                        evaluated = quality.cache[rollback]
                        verification = evaluated.verification
                        trajectory.record("rollback_quality_gate", evaluated.gate)
                    gate = evaluated.gate
                stage = "termination"
                cognitive_state = cognitive.state(current, registry, scores, branch_controller.snapshot(), verification)
                self._log(f"Open weaknesses: {', '.join(cognitive_state.high_severity_weaknesses) or 'none'}")
                self._log("Coverage: " + ", ".join(f"{d}={v.value}" for d, v in cognitive_state.coverage))
                cognitive_arguments = {"cognitive_state": cognitive_state} if isinstance(self.termination, TerminationController) else {}
                decision = self.termination.evaluate(analysis=analysis, iterations=iterations,
                    verification=verification, scores=tuple(scores), weaknesses=registry.snapshot(),
                    repeated_critiques=repeats, **cognitive_arguments)
                if quality is not None:
                    from .core.termination import TerminationDecision
                    accepted = gate.decision in (GateDecision.ACCEPT_VERIFIED, GateDecision.ACCEPT_PROVISIONALLY)
                    at_cap = iterations >= analysis.reasoning_budget.max_cycles or cognitive.remaining <= 0
                    if accepted and iterations >= analysis.reasoning_budget.min_cycles:
                        if accepted_at is None:
                            accepted_at = iterations
                        if iterations-accepted_at >= self.config.post_acceptance_cycles or at_cap:
                            decision = TerminationDecision(StopReason.ACCEPTED_VERIFIED if gate.decision is GateDecision.ACCEPT_VERIFIED
                                else StopReason.ACCEPTED_PROVISIONALLY, "; ".join(gate.reasons))
                        else:
                            decision = TerminationDecision(None, "Bounded post-acceptance regression probe requested")
                    elif at_cap:
                        decision = TerminationDecision(StopReason.INCONCLUSIVE if gate.decision is GateDecision.BLOCKED
                            else StopReason.BUDGET_EXHAUSTED, "; ".join(gate.reasons))
                    elif decision.reason in (StopReason.QUALITY_THRESHOLD_REACHED, StopReason.VERIFIER_PASSED, StopReason.FAST_PATH,
                                             StopReason.NO_MATERIAL_IMPROVEMENT, StopReason.REPEATED_CRITIQUE):
                        decision = TerminationDecision(None, "Quality gate requires further investigation: " + "; ".join(gate.reasons))
                # Hard ceilings are enforced even when a custom policy wants to continue.
                if decision.reason is None and (iterations >= analysis.reasoning_budget.max_cycles or cognitive.remaining <= 0):
                    from .core.termination import TerminationDecision
                    decision = TerminationDecision(StopReason.BUDGET_EXHAUSTED, "Engine-enforced maximum cycles")
                trajectory.record("termination_decision", decision)
                if decision.reason is not None:
                    reason, explanation = decision.reason, decision.explanation
                    break
                if (iterations > 0 and iterations % self.config.meta_check_interval == 0
                        and cognitive.last_meta_iteration != iterations):
                    stage = "meta_check"
                    meta = self.meta_controller.check(cognitive_state)
                    trajectory.record("meta_check", meta, "meta_checks")
                    cognitive.priority_adjustments = dict(meta["priority_adjustments"])
                    cognitive.last_meta_iteration = iterations
                    cognitive_state = cognitive.state(current, registry, scores, branch_controller.snapshot(), verification)
                stage = "question_selection"
                context = SelectionContext(task, current, tuple(critiques), registry.open(), tuple(used),
                                           iterations, analysis.reasoning_budget.max_cycles - iterations,
                                           analysis.dimensions, analysis.reasoning_budget.target_cycles,
                                           verification, cognitive_state)
                selection = (self.selection_policy.select(cognitive_state, self.operators) if self.selection_policy is not None
                             else self.selector.select(context, self.operators, provider))
                if selection.operator not in self.operators:
                    raise ValueError(f"Unknown selected operator: {selection.operator}")
                if not hasattr(selection, "target"):
                    policy = UtilitySelectionPolicy()
                    enriched = policy.choose(policy.rank(cognitive_state, self.operators), selection.operator)
                    selection = replace(enriched, reason=selection.reason)
                trajectory.record("operator_selection", selection)
                trajectory.record("operator_utility", selection, "operator_utilities")
                used.append(selection.operator)
                for ranked in selection.ranking[:3]:
                    self._log(f"Operator candidate: {ranked.operator} utility={ranked.utility:.3f}")
                self._log(f"Selected {selection.operator} -> {selection.target.target_id}")
                stage = "question_generation"
                question = self.question_generator.generate(self.operators[selection.operator], selection.target,
                    question_id=f"Q{len(used):03d}", parent_step=len(trajectory.snapshot()["steps"])-1)
                trajectory.record("question", question, "questions")
                self._log(f"Question {question.question_id}: {question.question}")
                cognitive.consume()
                stage = "critique"
                before_ids = {w.id for w in registry.snapshot()}
                output = self.operators[selection.operator].execute(provider, task=task, candidate=current,
                    weaknesses=registry.snapshot(), question=question,
                    cognitive_context=to_data(cognitive.knowledge.compact()))
                target_id = question.target.target_id if question.target.target_type in (
                    TargetType.CLAIM, TargetType.ASSUMPTION, TargetType.WEAKNESS, TargetType.EVIDENCE_GAP) else None
                findings = registry.ingest(output["findings"], iterations, target_id)
                critique = Critique(current.candidate_id, selection.operator, output["summary"], findings)
                critiques.append(critique)
                trajectory.record("critique", critique, "critiques")
                trajectory.set("weaknesses", registry.snapshot())
                trajectory.record("weakness_snapshot", registry.snapshot())
                knowledge_changes = cognitive.knowledge.ingest(output, current.candidate_id)
                if output.get("reframing"):
                    cognitive.reframe(output["reframing"], task, current.candidate_id)
                outcome = cognitive.complete(self.operators[selection.operator], question, findings, before_ids, knowledge_changes)
                self._log(f"Information gain: {outcome.information_gain.level}")
                fingerprint = frozenset(w.id for w in findings)
                repeats = repeats + 1 if fingerprint and fingerprint == previous_fingerprint else 0
                previous_fingerprint = fingerprint
                self._log(f"{len(findings)} weaknesses identified; {len(registry.open())} open")
                synthesis = None
                stage = "branch_exploration"
                if branch_controller.should_branch(cognitive_state, self.operators[selection.operator]):
                    synthesis, explored = branch_controller.explore(task, current, self.operators[selection.operator],
                        question, analysis.dimensions, provider)
                    cognitive.enrich_outcome(explored, bool(synthesis.adopt))
                stage = "revision_plan"
                extras = {}
                if synthesis is not None:
                    extras["synthesis"] = synthesis
                if cognitive.reframings:
                    extras["reframing"] = cognitive.reframings[-1]
                plan = self.planner.plan(task, current, critique, registry.snapshot(), provider, **extras)
                trajectory.record("revision_plan", plan, "revision_plans")
                self._log("Revision plan generated")
                stage = "revision"
                current = self._candidate(provider, task, current, plan, registry, iteration=iterations+1)
                candidates.append(current)
                iterations = current.iteration
                verification = None  # A previous candidate's score is never attributed to a new one.
                trajectory.record("candidate", current, "candidates")
                cognitive.knowledge.observe_candidate(current)
                self._log(f"Candidate {current.candidate_id} generated")
                stage = "verification"
                verification = self._verify(verifier, task, current, trajectory, registry)
                scores.append(verification.score)
        except Exception as exc:
            trajectory.record("error", {"stage": stage, "type": type(exc).__name__, "message": str(exc),
                                         "traceback": traceback.format_exc()}, "errors")
            reason = StopReason.EXTERNAL_BLOCKER
            explanation = f"{stage} failed: {type(exc).__name__}: {exc}"
            self._log(explanation)
        if branch_controller is not None:
            branch_controller.close_active(explanation)
        final_candidate = candidates[-1] if candidates else None
        if quality is not None and quality.best_candidate_id is not None:
            final_candidate = next(c for c in candidates if c.candidate_id == quality.best_candidate_id)
            quality.restore(final_candidate.candidate_id, cognitive, registry)
            verification = quality.cache[final_candidate.candidate_id].verification
            # Selection is unchanged; later information applicable to the returned content is reconciled, not re-judged.
            quality.reconcile(final_candidate.candidate_id, trajectory.snapshot(), registry)
        if cognitive is not None and candidates:
            cognitive.state(final_candidate, registry, scores, branch_controller.snapshot(), verification)
        trajectory.set("weaknesses", registry.snapshot())
        trajectory.set("final_candidate_id", final_candidate.candidate_id if final_candidate else None)
        trajectory.set("termination", {"reason": reason, "explanation": explanation})
        trajectory.record("termination", {"reason": reason, "explanation": explanation})
        trajectory.set("completed_at", now())
        trajectory.set("latency_ms", round((perf_counter() - start) * 1000, 3))
        trajectory.aggregate_usage()
        answer = final_candidate.content if final_candidate else ""
        if quality is not None:
            quality.latest_candidate_id = candidates[-1].candidate_id if candidates else None
            trajectory.set("latest_candidate_id", quality.latest_candidate_id)
            final_gate, label = quality.finalize(final_candidate.candidate_id if final_candidate else None,
                                                incomplete=reason is StopReason.EXTERNAL_BLOCKER)
            gate_value = final_gate.decision.value
        else:
            gate_value, label = "BLOCKED", "INCOMPLETE" if reason is StopReason.EXTERNAL_BLOCKER else "INCONCLUSIVE"
            trajectory.set("acceptance_label", label)
            trajectory.set("best_candidate_id", final_candidate.candidate_id if final_candidate else None)
            trajectory.set("latest_candidate_id", candidates[-1].candidate_id if candidates else None)
            trajectory.set("scorecard", {"quality_gate": gate_value, "acceptance_label": label,
                "known_uncertainties": ["Legacy compatibility execution: no independent quality judgment was configured"]})
        result = EngineResult(answer, trajectory.id, iterations, verification, reason, "",
            quality.best_candidate_id if quality else (final_candidate.candidate_id if final_candidate else None),
            candidates[-1].candidate_id if candidates else None, gate_value, label)
        saved_result = result.as_dict()
        saved_result.pop("trajectory_path")
        trajectory.set("final_result", saved_result)
        self._log(f"Termination: {reason.value}")
        # Persistence failures propagate; callers can recover last_trajectory for another store.
        try:
            path = self.ledger.save(trajectory.snapshot())
        except Exception as exc:
            trajectory.record("error", {"stage": "ledger_save", "type": type(exc).__name__, "message": str(exc)}, "errors")
            raise
        self._log(f"Trajectory saved: {path}")
        return replace(result, trajectory_path=path)

    def _candidate(self, provider, task, parent, plan, registry, *, iteration=None):
        iteration = iteration if iteration is not None else (parent.iteration + 1 if parent else 0)
        purpose = "revision" if parent else "initial_candidate"
        prompt = ("Produce a complete revised answer implementing the explicit revision plan. Retain requirements "
                  "already satisfied and state material limitations. Do not claim unperformed verification."
                  if parent else "Produce an initial answer to the task. State assumptions and material limitations.")
        response = provider.generate_structured(ModelRequest(purpose, prompt,
            {"task": task, "iteration": iteration, "candidate": to_data(parent), "revision_plan": to_data(plan)},
            CANDIDATE)).content
        validate(response, CANDIDATE)
        return Candidate(f"C{iteration}", parent.candidate_id if parent else None, iteration,
                         response["content"], now(), tuple(response["known_strengths"]),
                         registry.snapshot(), response["confidence"])

    def _verify(self, verifier, task, candidate, trajectory, registry):
        result = verifier.verify(task, candidate, trajectory.snapshot())
        if not isinstance(result, VerificationResult):
            trajectory.record("invalid_verification", {"candidate_id": candidate.candidate_id, "raw_repr": repr(result)})
            raise ValueError("Verifier must return VerificationResult")
        raw = result.as_dict()
        data = {key: value for key, value in raw.items() if key != "verifier"}
        try:
            if not result.dimensions or len(dict(result.dimensions)) != len(result.dimensions):
                raise ValueError("Verifier dimensions must be nonempty and unique")
            validate(data, verification_schema(dict(result.dimensions)))
        except Exception:
            trajectory.record("invalid_verification", {"candidate_id": candidate.candidate_id, "raw_repr": repr(result)})
            raise
        trajectory.record("verification", {"candidate_id": candidate.candidate_id, **raw,
            "evidence_type": "EXECUTED_EVIDENCE" if result.verifier == "basic_rules" else "MODEL_JUDGMENT"}, "verification")
        for transition in registry.apply_updates(result.weakness_updates):
            trajectory.record("weakness_status_change", transition)
        trajectory.set("weaknesses", registry.snapshot())
        self._log(f"Verification score: {result.score:.3f}")
        return result
