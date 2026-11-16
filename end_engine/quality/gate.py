from ..cognition.state import AssumptionStatus, CoverageLevel
from .grounding import ungrounded_objection
from .state import GateDecision, GateResult, Verdict


class QualityGate:
    def __init__(self, min_confidence=0.75, min_dimension_score=0.75):
        self.min_confidence, self.min_dimension_score = min_confidence, min_dimension_score

    def evaluate(self, *, candidate_id, verification, judgments, adversarial, cognitive_state=None,
                 validations=(), audits=(), dispute=None, comparison=None, trajectory_quality=None,
                 evidence=(), gaming=(), independent=True, integrity=None, engine_check=None):
        all_judgments = tuple(judgments)+tuple(adversarial)
        if not judgments or not adversarial:
            return GateResult(candidate_id, GateDecision.BLOCKED, ("Independent and adversarial judgments are required",))
        # v0.3.5: only decisive (grounded) findings count as defects. A judgment whose every serious objection is
        # misattributed, ungrounded or premise-dependent cannot drive REJECT/REVISE through its verdict either.
        deciding = tuple(j for j in all_judgments if j.assessment_decisive and not ungrounded_objection(j))
        fatal = [i for j in all_judgments for i in j.fatal_issues if i.decisive]
        fatal += [i for j in all_judgments for i in (*j.major_issues, *j.minor_issues) if i.fatal and i.decisive]
        if fatal or any(v.status == "CONTRADICTED" and v.importance == "HIGH" for v in validations):
            return GateResult(candidate_id, GateDecision.REJECT, tuple(i.description for i in fatal) or
                              ("A high-impact claim contradicts executed evidence",), ("Remove the demonstrated failure before acceptance",))
        if comparison and comparison.assessment_decisive and comparison.net_assessment == "SEVERE_REGRESSION":
            return GateResult(candidate_id, GateDecision.REJECT, (comparison.reason,), ("Restore the lost invariant",))
        if dispute:
            return GateResult(candidate_id, GateDecision.BLOCKED, ("DISPUTED: judges disagree",),
                              tuple(f"Independently verify {d}" for d in dispute.disputed_dimensions))
        reasons = [i.description for j in all_judgments for i in j.major_issues if i.decisive]
        if engine_check:  # deterministic, ENGINE_DERIVED task-constraint checks
            if engine_check.get('mandatory_revision'):
                reasons.append('Caller-declared mandatory revision requirement remains outstanding')
            if engine_check.get("format_violations"):
                reasons.append("Candidate does not follow the task's required output format: "
                               + "; ".join(engine_check["format_violations"]))
            if engine_check.get("internal_leakage"):
                reasons.append("Candidate exposes Engine internals not requested by the task: "
                               + "; ".join(engine_check["internal_leakage"][:5]))
            if engine_check.get('epistemic_overclaims'):
                reasons.append('Candidate epistemic status exceeds scoped executed evidence: '
                               + '; '.join(c['target'] for c in engine_check['epistemic_overclaims']))
            if engine_check.get('answer_region_ambiguous'):
                return GateResult(candidate_id, GateDecision.BLOCKED, ('Answer-region extraction is ambiguous',))
            if engine_check.get('evidence_violations'):
                reasons.extend(c['description'] for c in engine_check['evidence_violations'])
        reasons += [a.reason for a in audits if a.status == "INVALID"]
        reasons += [i.description for i in gaming]
        if any(j.verdict in (Verdict.FAIL, Verdict.NEEDS_REVISION) for j in deciding):
            reasons.append("At least one judge requires correction")
        if any(j.recommended_action in ("REJECT", "REVISE") for j in deciding):
            reasons.append("A judge's recommended action requires correction")
        if any(v.score < self.min_dimension_score for j in deciding for _,v in j.dimensions):
            reasons.append("A judged dimension is below the quality floor")
        if not verification or verification.assessment_decisive and (not verification.passed or verification.remaining_issues):
            reasons.append("Basic verification has not passed")
        if cognitive_state:
            if cognitive_state.high_severity_weaknesses:
                reasons.append("Unresolved high-severity weaknesses remain")
            if cognitive_state.active_branches:
                reasons.append("Unresolved branches remain")
            if any(a.decisive and a.risk in ("HIGH", "CRITICAL") and a.status in (AssumptionStatus.UNTESTED, AssumptionStatus.WEAKENED)
                   for a in cognitive_state.assumptions):
                reasons.append("Severe assumptions remain untested")
            if cognitive_state.complexity == "critical":
                major = {"correctness", "architecture", "assumptions", "failure_modes", "evidence", "alternatives", "safety", "second_order_effects"}
                if any(d in major and level is CoverageLevel.NONE for d,level in cognitive_state.coverage):
                    reasons.append("Critical scrutiny coverage is incomplete")
        if trajectory_quality and any("rejected branch" in issue for issue in trajectory_quality.trajectory_issues):
            return GateResult(candidate_id, GateDecision.REJECT, ("Synthesis imported a rejected branch",))
        if reasons:
            return GateResult(candidate_id, GateDecision.REVISE, tuple(dict.fromkeys(reasons)), ("Address judged findings through targeted cognition",))
        if (verification and verification.assessment_requires_evidence or
                any(j.assessment_requires_evidence for j in all_judgments)):
            return GateResult(candidate_id, GateDecision.BLOCKED,
                ('Assessment requires evidence; advisory model negatives do not establish candidate failure',),
                ('Investigate the unvalidated concern without treating it as a proven defect',))
        uncertain = [u for j in all_judgments for u in j.uncertainties]
        if verification and (verification.advisory_issues or not verification.assessment_decisive and not verification.passed):
            uncertain.append('Unvalidated model verification remains advisory; it is not a demonstrated defect or proof')
        nondecisive = [f"{j.judgment_id} {i.grounding}" for j in all_judgments
                       for i in (*j.fatal_issues, *j.major_issues, *j.minor_issues) if not i.decisive]
        if nondecisive:
            uncertain.append("Judge findings not grounded in the candidate were not counted as defects: "
                             + ", ".join(dict.fromkeys(nondecisive)))
        if engine_check and engine_check.get("consensus_as_confirmation"):
            uncertain.append("Candidate presents reported agreement as confirmation; agreement is not verification")
        if any(j.verdict is Verdict.INCONCLUSIVE for j in all_judgments):
            return GateResult(candidate_id, GateDecision.BLOCKED, ("Judgment is inconclusive",))
        if any(v.confidence < self.min_confidence for j in all_judgments for _,v in j.dimensions):
            uncertain.append("Judge confidence is below the verification threshold")
        if any(v.status == "UNVERIFIED" for v in validations):
            uncertain.append("Important claims have no candidate-bound executed support")
        if any(a.status == "WEAKLY_SUPPORTED" for a in audits):
            uncertain.append("Status transitions have only model-based support")
        # An accepted risk is a retained, unresolved concern; it can never support verified acceptance.
        risks = [a.target_id for a in audits if getattr(a, "transition", "") in ("accepted_risk", "ACCEPTED_RISK")
                 and a.status != "INVALID"]
        if risks:
            uncertain.append("Accepted risks remain unverified: " + ", ".join(risks))
        if not independent:
            uncertain.append("Generator and judge share model identity")
        # Invalid or out-of-scope references, contradictions and model-asserted support stay visible as uncertainty:
        # they prevent verified acceptance but are never converted into a failure.
        if integrity is not None:
            uncertain += list(integrity.uncertainties)
        executed = [e for e in evidence if e.candidate_id == candidate_id and e.evidence_type == "EXECUTED_EVIDENCE"]
        if any(not e.passed for e in executed):
            return GateResult(candidate_id, GateDecision.REVISE, ("An executed check failed",))
        if not executed:
            uncertain.append("No executed evidence is attached")
        if uncertain:
            return GateResult(candidate_id, GateDecision.ACCEPT_PROVISIONALLY, tuple(dict.fromkeys(uncertain)))
        return GateResult(candidate_id, GateDecision.ACCEPT_VERIFIED,
                          ("Independent judgments and candidate-bound executed checks agree within the recorded scope",))
