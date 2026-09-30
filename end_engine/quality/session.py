from copy import deepcopy
from dataclasses import dataclass, replace

from ..cognition.state import AssumptionStatus
from ..core.state import to_data, Weakness, WeaknessStatus, WeaknessUpdate
from .audits import ClaimValidator, ResolutionAuditor, TrajectoryJudge, VerifierGamingDetector
from .comparison import RevisionComparator
from .gate import QualityGate
from .integrity import (ENGINE_EVIDENCE_PREFIX, EvidenceIndex, EvidenceIntegrity, identical_content_findings,
                        integrity_summary)
from .judges import AdversarialJudge, AdversarialTestGenerator, CandidateJudge, detect_disagreement
from .providers import recorded_judge
from .state import CheckContract, EvidenceArtifact, GateDecision, GateResult


@dataclass(frozen=True)
class CandidateAssessment:
    candidate_id: str
    gate: GateResult
    verification: object
    judgments: tuple
    adversarial: tuple
    comparison: object
    trajectory_quality: object
    integrity: object = None


class QualitySession:
    def __init__(self, config, trajectory, generator_metadata, judge, secondary=None, adversary=None, tool_verifier=None):
        self.config, self.trajectory, self.tool_verifier = config, trajectory, tool_verifier
        self.primary = recorded_judge(judge, trajectory, "primary_judge")
        self.secondary = recorded_judge(secondary, trajectory, "secondary_judge") if secondary else None
        self.adversary = recorded_judge(adversary or judge, trajectory, "adversarial_judge")
        self.gate = QualityGate(config.judge_min_confidence)
        self.comparator = RevisionComparator(self.primary)
        self.cache, self.snapshots, self.candidates = {}, {}, {}
        self.best_candidate_id = None
        self.latest_candidate_id = None
        self.final_gate = None  # Set only by reconcile() for the returned candidate.
        self.last_rejected = False
        self.engine_evidence = set()  # (claim_id, status, evidence) knowledge updates written by this session
        generator_identity = (generator_metadata.get("provider"), generator_metadata.get("model"))
        identities = [(p.metadata().get("provider"), p.metadata().get("model"))
                      for p in (judge, secondary, adversary or judge) if p is not None]
        self.independent = all(generator_identity != identity for identity in identities)
        self.trajectory.set("judge_configuration", {"primary": judge.metadata(), "secondary": secondary.metadata() if secondary else None,
            "adversarial": (adversary or judge).metadata(), "different_model_identity": self.independent,
            "blinded_candidates": True})

    def evaluate(self, task, candidate, parent, verification, cognitive, registry, branches, scores):
        if candidate.candidate_id in self.cache:
            return self.cache[candidate.candidate_id], None
        self.latest_candidate_id = candidate.candidate_id
        self.candidates[candidate.candidate_id] = candidate
        claims = tuple(cognitive.knowledge.claims[c] for c in cognitive.knowledge.current_claim_ids)
        tests = AdversarialTestGenerator(self.adversary).generate(task, candidate, claims,
            1+len(self.trajectory.snapshot()["adversarial_tests"]),
            targets=tuple({"id": w.id, "description": w.description} for w in registry.snapshot())+
                    tuple({"id": a.assumption_id, "description": a.statement} for a in cognitive.knowledge.assumptions.values()))
        for test in tests:
            self.trajectory.record("adversarial_test", test, "adversarial_tests")
        evidence = tuple(self.tool_verifier.collect(task, candidate, tests, claims)) if self.tool_verifier else ()
        seen = set()
        for artifact in evidence:
            if (not isinstance(artifact, EvidenceArtifact) or artifact.candidate_id != candidate.candidate_id
                    or artifact.artifact_id in seen or artifact.evidence_type not in ("EXECUTED_EVIDENCE", "MODEL_JUDGMENT")
                    or type(artifact.passed) is not bool or artifact.contract is not None and (
                        not isinstance(artifact.contract, CheckContract) or artifact.contract.phase not in ("development", "final"))):
                raise ValueError("Invalid or incorrectly scoped tool evidence")
            seen.add(artifact.artifact_id)
            self.trajectory.record("verifier_evidence", artifact, "verifier_evidence")
        dimensions = tuple(dict.fromkeys((*cognitive.analysis.dimensions, "constraint_adherence")))
        judgments = []
        for provider, name in ((self.primary, "primary"), (self.secondary, "secondary")):
            if provider:
                result = CandidateJudge(provider, name).judge(task, candidate, dimensions, claims, evidence,
                    f"J{len(self.trajectory.snapshot()['judgments'])+1:03d}")
                self.trajectory.record("judgment", result.as_dict(), "judgments")
                judgments.append(result)
        adversarial = AdversarialJudge(self.adversary).judge(task, candidate, dimensions, claims, evidence,
            f"AJ{len(self.trajectory.snapshot()['adversarial_judgments'])+1:03d}")
        self.trajectory.record("adversarial_judgment", adversarial.as_dict(), "adversarial_judgments")
        all_judgments = (*judgments, adversarial)
        dispute = detect_disagreement(judgments)  # Adversarial objections are handled as findings, never averaged.
        if dispute:
            self.trajectory.record("judge_dispute", dispute, "disputes")
        for judgment in all_judgments:
            for issue in (*judgment.fatal_issues, *judgment.major_issues, *judgment.minor_issues):
                if issue.fatal:
                    self.trajectory.record("fatal_issue", {"candidate_id": candidate.candidate_id,
                        "judgment_id": judgment.judgment_id, **to_data(issue)}, "fatal_issues")
        validations = ClaimValidator().validate(claims, candidate.candidate_id, evidence, content=candidate.content)
        for validation in validations:
            self.trajectory.record("claim_validation", {"candidate_id": candidate.candidate_id, **to_data(validation)}, "claim_validations")
            if validation.status in ("SUPPORTED", "CONTRADICTED"):
                text = ENGINE_EVIDENCE_PREFIX + ", ".join(validation.supporting_artifacts+validation.contradicting_artifacts)
                if cognitive.knowledge.update(validation.claim_id, validation.status, text):
                    self.engine_evidence.add((validation.claim_id, validation.status, text))
        record = self.trajectory.snapshot()
        resolutions = ResolutionAuditor().audit(record, candidate, evidence, judgments=all_judgments)
        assumptions = ResolutionAuditor().audit(record, candidate, evidence, assumptions=True, judgments=all_judgments)
        for collection, items in (("resolution_audits", resolutions), ("assumption_audits", assumptions)):
            for audit in items:
                self.trajectory.record(collection[:-1], {"candidate_id": candidate.candidate_id, **to_data(audit)}, collection)
        comparison = None
        if parent:
            comparison = self.comparator.compare(task, parent, candidate, (*dimensions, "complexity_cost"))
            self.trajectory.record("pairwise_comparison", comparison, "pairwise_comparisons")
            self.trajectory.record("quality_delta", comparison, "quality_deltas")
            bad = comparison.net_assessment in ("REGRESSION", "SEVERE_REGRESSION") or comparison.preferred == parent.candidate_id
        gaming = VerifierGamingDetector().detect(task, candidate, parent, evidence=evidence, reframings=record.get("reframings", ()))
        for issue in gaming:
            self.trajectory.record("gaming_signal", {"candidate_id": candidate.candidate_id, **to_data(issue)}, "gaming_signals")
        assessment = TrajectoryJudge().assess(record, (*resolutions, *assumptions), (), independent=self.independent, evidence=evidence)
        self.trajectory.record("trajectory_judgment", {"candidate_id": candidate.candidate_id, **to_data(assessment)}, "trajectory_judgments")
        # An INVALID audit is a procedural failure, not a candidate defect: the unsupported transition is rejected and
        # the audited concern stays unresolved at its own severity (serious concerns still escalate through it).
        for audit in (*resolutions, *assumptions):
            if audit.status == "INVALID":
                self._reject_transition(audit, candidate, registry, cognitive)
        # Findings become structured cognitive targets. Judges never rewrite an answer.
        feedback = [issue for judgment in all_judgments for issue in (*judgment.fatal_issues, *judgment.major_issues)] + list(gaming)
        for issue in feedback:
            category = {"constraint_violation": "constraint", "unsupported_claim": "evidence", "rollback_flaw": "failure_mode",
                        "contradiction": "counterexample", "unsupported_certainty": "evidence"}.get(issue.category, issue.category)
            existing = next((w for w in registry.snapshot() if w.description == issue.description), None)
            found = registry.ingest([{"weakness_id": existing.id if existing else None, "type": category,
                "severity": "critical" if issue.fatal else "high", "description": issue.description,
                "evidence": ", ".join(issue.evidence) or "Independent judge finding; further verification required"}],
                candidate.iteration, issue.target)
            self.trajectory.record("judge_feedback", {"candidate_id": candidate.candidate_id, "target": issue.target,
                "weakness_ids": [w.id for w in found], "issue": issue}, "judge_feedback")
        self.trajectory.set("weaknesses", registry.snapshot())
        # Evidence integrity: model references are resolved against recorded evidence; nothing is repaired or dropped.
        record = self.trajectory.snapshot()
        steps = {s["step"]: s["data"] for s in record["steps"]}
        created = max((s["step"] for s in record["steps"] if s["type"] == "candidate"
                       and s["data"]["candidate_id"] == candidate.candidate_id), default=-1)
        # Only rationales for transitions made in this candidate's scope; older ones belong to earlier candidates.
        transitions = tuple((f"{a.target_id}.{'evidence' if a.kind == 'assumption' else 'status_reason'}@step{a.transition_step}",
                             steps.get(a.transition_step, {}).get("after", {}).get("evidence" if a.kind == "assumption" else "status_reason", ""))
                            for a in (*resolutions, *assumptions) if a.transition_step > created)
        index = EvidenceIndex(record, candidate, evidence=evidence, judgments=all_judgments,
            claims=tuple(cognitive.knowledge.claims.values()), weaknesses=tuple(registry.snapshot()),
            assumptions=tuple(cognitive.knowledge.assumptions.values()))
        integrity = EvidenceIntegrity().assess(candidate, claims, evidence, all_judgments, validations, index,
            audits=(*resolutions, *assumptions), transitions=transitions, independent=self.independent,
            engine_evidence=self.engine_evidence)
        self.trajectory.record("evidence_integrity", integrity, "evidence_integrity")
        state = cognitive.state(candidate, registry, scores, branches, verification)
        gate = self.gate.evaluate(candidate_id=candidate.candidate_id, verification=verification,
            judgments=tuple(judgments), adversarial=(adversarial,), cognitive_state=state,
            validations=validations, audits=(*resolutions, *assumptions), dispute=dispute, comparison=comparison,
            trajectory_quality=assessment, evidence=evidence, gaming=gaming, independent=self.independent,
            integrity=integrity)
        self.trajectory.record("quality_gate", gate, "quality_gate_decisions")
        if comparison:
            label = ("BAD_REVISION" if bad or gate.decision is GateDecision.REJECT else
                     "NO_MATERIAL_CHANGE" if comparison.net_assessment == "NO_MATERIAL_CHANGE" else
                     "RECOVERY_REVISION" if self.last_rejected else "GOOD_REVISION")
            self.trajectory.record("transition_label", {"from_candidate": parent.candidate_id,
                "to_candidate": candidate.candidate_id, "label": label}, "transition_labels")
        result = CandidateAssessment(candidate.candidate_id, gate, verification, tuple(judgments), (adversarial,), comparison,
                                     assessment, integrity)
        self.cache[candidate.candidate_id] = result
        self.snapshots[candidate.candidate_id] = (registry.snapshot(), deepcopy(cognitive.knowledge.claims),
            deepcopy(cognitive.knowledge.assumptions), cognitive.knowledge.current_claim_ids)
        prior = self.cache.get(self.best_candidate_id)
        best_comparison = comparison
        if prior and parent and parent.candidate_id != self.best_candidate_id:
            best_comparison = self.comparator.compare(task, self.candidates[self.best_candidate_id], candidate,
                                                       (*dimensions, "complexity_cost"))
            self.trajectory.record("best_candidate_comparison", best_comparison, "pairwise_comparisons")
        ranks = {GateDecision.REJECT: 0, GateDecision.BLOCKED: 1, GateDecision.REVISE: 2,
                 GateDecision.ACCEPT_PROVISIONALLY: 3, GateDecision.ACCEPT_VERIFIED: 4}
        if prior is None or (gate.decision is not GateDecision.REJECT and
            (ranks[gate.decision] > ranks[prior.gate.decision] or ranks[gate.decision] == ranks[prior.gate.decision]
             and best_comparison and best_comparison.preferred == candidate.candidate_id
             and best_comparison.net_assessment != "SEVERE_REGRESSION")):
            self.best_candidate_id = candidate.candidate_id
        rollback = None
        if self.best_candidate_id != candidate.candidate_id and (gate.decision is GateDecision.REJECT or
                comparison and comparison.net_assessment == "SEVERE_REGRESSION"):
            rollback = self.best_candidate_id
            self.trajectory.record("candidate_rollback", {"from_candidate": candidate.candidate_id, "to_candidate": rollback,
                "reason": comparison.reason if comparison else "; ".join(gate.reasons)}, "rollback_events")
        self.last_rejected = gate.decision is GateDecision.REJECT or bool(comparison and comparison.net_assessment in ("REGRESSION", "SEVERE_REGRESSION"))
        self.trajectory.set("best_candidate_id", self.best_candidate_id)
        self.trajectory.set("latest_candidate_id", self.latest_candidate_id)
        return result, rollback

    def _reject_transition(self, audit, candidate, registry, cognitive):
        reason = f"Unsupported transition to {audit.transition or 'a resolved status'} rejected by audit: {audit.reason}"
        action = "target_unavailable"
        if audit.kind == "weakness":
            current = next((w for w in registry.snapshot() if w.id == audit.target_id), None)
            if current is not None and current.status is not WeaknessStatus.OPEN:
                for change in registry.apply_updates((WeaknessUpdate(current.id, WeaknessStatus.OPEN, reason),)):
                    self.trajectory.record("weakness_status_change", {**change, "source": "resolution_audit",
                                                                      "audit_transition_step": audit.transition_step})
                action = "reopened"
            elif current is not None:
                action = "already_open"
        elif audit.target_id in cognitive.knowledge.assumptions:
            changed = cognitive.knowledge.update(audit.target_id, AssumptionStatus.UNTESTED.value, reason, assumption=True)
            action = "reset_to_untested" if changed else "already_untested"
        if audit.kind == "weakness":
            target = next((w for w in registry.snapshot() if w.id == audit.target_id), None)
            severity = target.severity if target else None
        else:
            severity = getattr(cognitive.knowledge.assumptions.get(audit.target_id), "risk", None)
        self.trajectory.record("audit_failure", {"candidate_id": candidate.candidate_id, "kind": audit.kind,
            "target_id": audit.target_id, "transition": audit.transition, "transition_step": audit.transition_step,
            "reason": audit.reason, "criteria_gaps": audit.criteria_gaps, "action": action,
            "retained_severity": severity, "new_weakness_created": False})

    def restore(self, identity, cognitive, registry):
        weaknesses, claims, assumptions, current_claims = self.snapshots[identity]
        registry.restore(weaknesses)
        cognitive.knowledge.claims = deepcopy(claims)
        cognitive.knowledge.assumptions = deepcopy(assumptions)
        cognitive.knowledge.current_claim_ids = current_claims
        self.trajectory.record("candidate_state_restored", {"candidate_id": identity, "weaknesses": weaknesses,
            "claims": tuple(claims.values()), "assumptions": tuple(assumptions.values())})
        # Historical knowledge discoveries remain in step events, including failed revisions.
        self.trajectory.set("claims", tuple(claims.values()))
        self.trajectory.set("assumptions", tuple(assumptions.values()))

    def reconcile(self, final_candidate_id, record, registry):
        """Final assessment of the returned candidate, including later information applicable to its exact content.

        No model is called. The returned candidate's own recorded evaluation stays immutable; the reconciliation is
        recorded separately with its basis. Applied: findings from critiques of byte-identical candidates recorded after
        the returned candidate's gate, and status transitions made on byte-identical candidates that an audit in that same
        content scope validated. Not applied: transitions on different content, invalid or unaudited transitions, and
        candidate-scoped judge feedback or audit failures (reported; judge feedback caps acceptance at provisional).
        Integrity findings of byte-identical candidates: content-related conflicts are reported as unresolved (capping
        acceptance at provisional) unless validly resolved later; citation errors and process failures are only listed."""
        original = self.cache[final_candidate_id].gate
        content = {c["candidate_id"]: c["content"] for c in record["candidates"]}
        same = {cid for cid, text in content.items() if text == content[final_candidate_id]}
        steps = record["steps"]
        boundary = next(s["step"] for s in steps if s["type"] == "quality_gate" and s["data"]["candidate_id"] == final_candidate_id)
        audits = [s["data"] for s in steps if s["type"] == "resolution_audit" and s["data"]["candidate_id"] in same]
        view = {w.id: to_data(w) for w in registry.snapshot()}  # State recorded at the returned candidate's evaluation.
        later, applied, ignored, not_transferred = {}, [], [], []
        owner = None
        for step in steps:
            kind, data = step["type"], step["data"]
            if kind == "candidate":
                owner = data["candidate_id"]
            if step["step"] <= boundary:
                continue
            if kind == "critique" and data["candidate_id"] in same:
                for finding in data["findings"]:
                    view[finding["id"]] = dict(finding)
                    later[finding["id"]] = {"source": "critique", "candidate_id": data["candidate_id"], "step": step["step"]}
            elif kind == "weakness_status_change" and not data.get("source") and data["after"]["id"] in view:
                after = data["after"]
                entry = {"target_id": after["id"], "status": after["status"], "step": step["step"], "candidate_id": owner}
                verdicts = [a["status"] for a in audits if a["transition_step"] == step["step"]]
                if owner not in same:
                    ignored.append({**entry, "reason": "transition made on different content"})
                elif verdicts and verdicts[-1] in ("VALID", "WEAKLY_SUPPORTED"):
                    view[after["id"]] = {**view[after["id"]], "status": after["status"], "status_reason": after["status_reason"]}
                    later.setdefault(after["id"], {"source": "validated_transition", "candidate_id": owner, "step": step["step"]})
                    applied.append({**entry, "audit": verdicts[-1]})
                else:
                    ignored.append({**entry, "reason": "rejected by audit" if verdicts else "not audited in this content scope"})
            elif kind in ("judge_feedback", "audit_failure") and data["candidate_id"] in same - {final_candidate_id}:
                not_transferred.append({"kind": kind, "candidate_id": data["candidate_id"], "step": step["step"],
                    "target_ids": list(data.get("weakness_ids") or [data.get("target_id")]),
                    "reason": "candidate-scoped judgment or procedure; identical content alone does not establish applicability"})
        # Integrity findings of byte-identical candidates (recorded before or after this gate): content-related
        # conflicts stay unresolved and visible; citation errors and candidate-specific process failures are listed only.
        resolved = {a["target_id"]: a["step"] for a in applied
                    if a["audit"] == "VALID" and view[a["target_id"]]["status"] == "resolved"}
        applicable, resolved_later, listed, integrity_uncertain = identical_content_findings(
            [(s["step"], s["data"]) for s in steps if s["type"] == "evidence_integrity" and s["data"]["candidate_id"] in same],
            final_candidate_id, resolved)
        not_transferred += listed
        reasons, uncertain = [], list(integrity_uncertain)
        high = [i for i in later if view[i]["status"] == "open" and view[i]["severity"] in ("high", "critical")]
        if high:
            reasons.append("Unresolved high-severity concern applicable to the returned content: " + ", ".join(high))
        risks = [i for i in later if view[i]["status"] == "accepted_risk"]
        if risks:
            uncertain.append("Accepted risks remain unverified: " + ", ".join(risks))
        unaudited = [t["target_id"] for t in ignored if t["reason"] == "not audited in this content scope"]
        if unaudited:
            uncertain.append("Unaudited status transitions were not applied: " + ", ".join(dict.fromkeys(unaudited)))
        judged = [f"{t} (judgment of {n['candidate_id']})" for n in not_transferred if n["kind"] == "judge_feedback" for t in n["target_ids"]]
        if judged:
            uncertain.append("Applicability undetermined for findings from judgments of identical content: " + ", ".join(judged))
        ranks = {GateDecision.REJECT: 0, GateDecision.BLOCKED: 1, GateDecision.REVISE: 2,
                 GateDecision.ACCEPT_PROVISIONALLY: 3, GateDecision.ACCEPT_VERIFIED: 4}
        decision = original.decision
        if high and ranks[decision] > ranks[GateDecision.REVISE]:
            decision = GateDecision.REVISE
        elif uncertain and decision is GateDecision.ACCEPT_VERIFIED:
            decision = GateDecision.ACCEPT_PROVISIONALLY
        gate = original
        if reasons or uncertain:
            gate = GateResult(final_candidate_id, decision, tuple(dict.fromkeys((*original.reasons, *reasons, *uncertain))),
                original.required_actions + (("Address concerns applicable to the returned content",) if high else ()))
        registry.restore(tuple(Weakness(**{**w, "status": WeaknessStatus(w["status"])}) for w in view.values()))
        reconciliation = {"final_candidate_id": final_candidate_id, "evaluation_step": boundary,
            "identical_content_candidates": sorted(same), "original_gate": original, "reconciled_gate": gate,
            "changed": gate != original, "later_applicable_concerns": [{**view[i], "provenance": later[i]} for i in later],
            "unresolved_concerns": [view[i] for i in view if view[i]["status"] in ("open", "accepted_risk")],
            "applied_transitions": applied, "ignored_transitions": ignored, "not_transferred": not_transferred,
            "integrity_findings": {"applicable": applicable, "resolved_later": resolved_later},
            "model_calls": 0, "basis": "byte-identical content; events after the returned candidate's gate; "
                                       "same-scope validated transitions only"}
        self.trajectory.record("final_reconciliation", reconciliation)
        self.trajectory.set("final_reconciliation", reconciliation)
        self.final_gate = gate
        return gate

    def finalize(self, final_candidate_id, *, incomplete=False):
        result = self.cache.get(final_candidate_id)
        gate = result.gate if result else GateResult(final_candidate_id or "", GateDecision.BLOCKED, ("No complete evaluation",))
        if self.final_gate is not None and self.final_gate.candidate_id == final_candidate_id:
            gate = self.final_gate
        if incomplete:
            # Budget or execution stops stay BLOCKED/INCOMPLETE, but applicable reconciled concerns remain reported.
            added = tuple(r for r in gate.reasons if result is None or r not in result.gate.reasons)
            gate = GateResult(final_candidate_id or "", GateDecision.BLOCKED,
                              ("Execution failed before the quality process completed", *added))
        label = ("INCOMPLETE" if incomplete else "ACCEPTED_HIGH_CONFIDENCE" if gate.decision is GateDecision.ACCEPT_VERIFIED else
            "ACCEPTED_PROVISIONAL" if gate.decision is GateDecision.ACCEPT_PROVISIONALLY else
            "REJECTED_FATAL" if any(j.fatal_issues for j in (*result.judgments,*result.adversarial)) else
            "REJECTED_REGRESSION" if result and result.comparison and "REGRESSION" in result.comparison.net_assessment else "INCONCLUSIVE") if result else "INCOMPLETE"
        self.trajectory.set("acceptance_label", label)
        profile = to_data(result.trajectory_quality) if result else None
        if profile is not None:
            profile["operator_efficiency"] = "LOW" if profile["redundancy"] == "HIGH" else "MEDIUM"
            profile["adversarial_resilience"] = "HIGH" if gate.decision is GateDecision.ACCEPT_VERIFIED else "MEDIUM" if gate.decision is GateDecision.ACCEPT_PROVISIONALLY else "LOW"
            profile["rejected_revisions"] = len(self.trajectory.snapshot()["rollback_events"])
        uncertainties = [u for j in (*result.judgments, *result.adversarial) for u in j.uncertainties] if result else []
        if gate.decision is not GateDecision.ACCEPT_VERIFIED:
            uncertainties += list(gate.reasons)
        reconciliation = self.trajectory.snapshot().get("final_reconciliation") or {}
        integrity = integrity_summary(result.integrity) if result else None
        if integrity is not None:
            integrity["identical_content_findings"] = (reconciliation.get("integrity_findings") or {}).get("applicable", [])
        self.trajectory.set("scorecard", {"final_candidate": final_candidate_id, "best_candidate": self.best_candidate_id,
            "latest_candidate": self.latest_candidate_id, "quality_gate": gate.decision.value,
            "trajectory": profile, "known_uncertainties": list(dict.fromkeys(uncertainties)), "acceptance_label": label,
            "unresolved_concerns": [{k: w[k] for k in ("id", "severity", "status")}
                                    for w in reconciliation.get("unresolved_concerns", ())],
            "final_reconciliation_changed": bool(reconciliation.get("changed")),
            # The returned candidate's own evidence view: anything short of verified stays listed with its reason.
            "evidence_integrity": integrity})
        return gate, label
