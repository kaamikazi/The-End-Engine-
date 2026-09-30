import re

from .integrity import artifact_mismatch, content_sha256, scope_gap
from .state import ClaimValidationResult, JudgeIssue, ResolutionAudit, TrajectoryAssessment, Verdict

# Accepting a risk leaves the concern unresolved on purpose; it is never verification. Without executed evidence
# or a targeted revision, it is admissible only when every criterion below holds, and then only as WEAKLY_SUPPORTED.
RISK_ACCEPTABLE_SEVERITIES = ("low", "medium")
MIN_RISK_JUSTIFICATION = 40


class ClaimValidator:
    def validate(self, claims, candidate_id, evidence, content=None):
        """Support comes only from passed executed checks of this candidate whose declared scope covers the claim.
        A passed check outside that scope is reported as out of scope; a failed check contradicts the claim only when it
        checked this exact artifact (or declares no artifact binding)."""
        digest = content_sha256(content) if content is not None else None
        results = []
        for claim in claims:
            relevant = [e for e in evidence if e.candidate_id == candidate_id and claim.claim_id in e.targets
                        and e.evidence_type == "EXECUTED_EVIDENCE"]
            support = tuple(e.artifact_id for e in relevant if e.passed and not scope_gap(e, claim, digest))
            outside = tuple(e.artifact_id for e in relevant if e.passed and scope_gap(e, claim, digest))
            contradict = tuple(e.artifact_id for e in relevant if not e.passed and not artifact_mismatch(e, digest))
            status = "CONTRADICTED" if contradict else "SUPPORTED" if support else (
                "NOT_APPLICABLE" if claim.evidence_status.value == "NOT_APPLICABLE" and claim.evidence else "UNVERIFIED")
            importance = "HIGH" if re.search(r"\b(guarantee\w*|always|never|must|prevent\w*|rollback|safe\w*)\b", claim.text, re.I) else "MEDIUM"
            results.append(ClaimValidationResult(claim.claim_id, status, importance, support, contradict,
                                                 0.95 if support or contradict else 0.4, outside))
        return tuple(results)


class ResolutionAuditor:
    @staticmethod
    def risk_acceptance_gaps(after, reason, candidate_id, evidence, judgments):
        """Unmet criteria for accepting a weakness as a risk without executed evidence or a targeted revision."""
        gaps = []
        if after.get("severity") not in RISK_ACCEPTABLE_SEVERITIES:
            gaps.append(f"severity {after.get('severity')!s} requires a targeted revision or executed evidence")
        text = " ".join(reason.split())
        if len(text) < MIN_RISK_JUSTIFICATION or text.lower() == " ".join(str(after.get("description", "")).split()).lower():
            gaps.append("justification is missing, too short, or only restates the concern")
        if any(e.candidate_id == candidate_id and e.evidence_type == "EXECUTED_EVIDENCE" and not e.passed for e in evidence):
            gaps.append("executed evidence for this candidate failed")
        bound = [j for j in judgments if j.candidate_id == candidate_id]
        if not any(j.adversarial for j in bound) or not any(not j.adversarial for j in bound):
            gaps.append("independent and adversarial judgments of this candidate are required")
        elif any(j.verdict is not Verdict.PASS or j.recommended_action != "ACCEPT" or j.fatal_issues or j.major_issues
                 for j in bound):
            gaps.append("independent judgments do not corroborate acceptance")
        return tuple(gaps)

    def audit(self, trajectory, candidate, evidence, *, assumptions=False, judgments=()):
        kind = "assumption_status_change" if assumptions else "weakness_status_change"
        transitions = {}
        revision = None
        for step in trajectory["steps"]:
            if step["type"] == "candidate":
                revision = step["data"]
            if step["type"] == kind:
                after = step["data"]["after"]
                identity = after.get("assumption_id", after.get("id"))
                transitions[identity] = (step, revision)
        audits = []
        for identity,(step,revision) in transitions.items():
            after = step["data"]["after"]
            if after["status"] not in ("resolved", "accepted_risk", "invalidated", "SUPPORTED", "INVALIDATED", "ACCEPTED_RISK"):
                continue
            refs = tuple(e.artifact_id for e in evidence if e.candidate_id == candidate.candidate_id
                         and identity in e.targets and e.passed and e.evidence_type == "EXECUTED_EVIDENCE"
                         and not artifact_mismatch(e, content_sha256(candidate.content)))
            reason = after.get("evidence", "") if assumptions else after.get("status_reason", "")
            parent = next((c for c in trajectory["candidates"] if revision and c["candidate_id"] == revision["parent_candidate_id"]), None)
            changed = bool(revision and parent and revision["content"].strip() != parent["content"].strip())
            plans = [p for p in trajectory["revision_plans"] if parent and p["candidate_id"] == parent["candidate_id"]]
            targeted = any(identity in change["targets"] for plan in plans for change in plan["changes"])
            # An invalidation with an explicit counterexample is useful but remains a model judgment.
            corroboration, gaps = (), ()
            if refs and reason.strip():
                status, explanation = "VALID", "Candidate-bound executed evidence supports this transition"
            elif len(reason.strip()) >= 20 and (changed and (targeted or assumptions)):
                status, explanation = "WEAKLY_SUPPORTED", "Substantive revision and rationale exist, but no executed support is attached"
            elif not assumptions and after["status"] == "accepted_risk":
                gaps = self.risk_acceptance_gaps(after, reason, candidate.candidate_id, evidence, judgments)
                if gaps:
                    status, explanation = "INVALID", "Risk acceptance does not meet criteria: " + "; ".join(gaps)
                else:
                    corroboration = tuple(j.judgment_id for j in judgments if j.candidate_id == candidate.candidate_id)
                    status, explanation = ("WEAKLY_SUPPORTED", "Justified lower-severity risk acceptance corroborated by "
                                           "independent judgments; model-based, the concern remains unverified")
            else:
                status, explanation = "INVALID", "Status label lacks a supporting targeted revision or evidence"
            audits.append(ResolutionAudit(identity, status, explanation, step["step"], refs,
                                           "assumption" if assumptions else "weakness", after["status"],
                                           corroboration, gaps))
        return tuple(audits)


class VerifierGamingDetector:
    def detect(self, task, candidate, parent=None, *, evidence=(), reframings=()):
        issues = []
        text = candidate.content.lower()
        if re.search(r"all (?:assumptions|claims|requirements|tests) (?:are |have been )?(?:verified|proven|passed|satisfied)", text) and not evidence:
            issues.append(JudgeIssue("unsupported_certainty", "Candidate asserts universal verification without supporting artifacts"))
        if parent and len(candidate.content) > max(200, len(parent.content)*1.6):
            old = set(re.findall(r"\w+", parent.content.lower()))
            new = set(re.findall(r"\w+", text))
            if len(new-old)/max(1,len(new)) < 0.2:
                issues.append(JudgeIssue("verbosity_without_substance", "Length increased substantially with little new content"))
        if sum(text.count(word) for word in ("correctness", "robustness", "completeness", "verified")) >= 12:
            issues.append(JudgeIssue("verifier_vocabulary", "Repeated verifier terminology is not evidence of compliance"))
        if parent:
            constraints = re.findall(r"\b(?:must|without|never)\s+([^.;\n]+)", task.lower())
            for constraint in constraints:
                terms = set(re.findall(r"\w+", constraint)) - {"a", "the", "to", "of", "use", "uses"}
                if terms and terms <= set(re.findall(r"\w+", parent.content.lower())) and not terms <= set(re.findall(r"\w+", text)):
                    issues.append(JudgeIssue("dropped_constraint", f"A previously explicit task constraint disappeared: {constraint}"))
        if reframings and any(term in text for term in ("ignore the original", "out of scope", "cannot guarantee anything")):
            issues.append(JudgeIssue("reframing_escape", "Candidate may be evading an original requirement with scope or caveats"))
        return tuple(issues)


class TrajectoryJudge:
    """Deterministic integrity checks independent of generator self-scores."""
    def assess(self, trajectory, audits, comparisons, *, independent=True, evidence=()):
        outcomes = trajectory.get("operator_outcomes", [])
        productive = sum(o["information_gain"]["level"] in ("HIGH", "MEDIUM") for o in outcomes)
        discoveries = {item["issue"]["description"] for item in trajectory.get("judge_feedback", [])}
        productive += len(discoveries) + sum(c["net_assessment"] in ("IMPROVEMENT", "STRONG_IMPROVEMENT")
                                             for c in trajectory.get("quality_deltas", []))
        redundant = sum(o["information_gain"]["level"] in ("LOW", "ZERO") for o in outcomes)
        issues = []
        if any(a.status == "INVALID" for a in audits):
            issues.append("One or more resolution or assumption transitions lack support")
        if outcomes and redundant > productive:
            issues.append("Operator effort is predominantly repetitive or low-information")
        rejected = {b["branch_id"] for b in trajectory.get("branches", []) if b["status"] == "REJECTED"}
        if any(a["branch"] in rejected for p in trajectory.get("synthesis_plans", []) for a in p["adopt"]):
            issues.append("Synthesis imported a rejected branch")
        return TrajectoryAssessment("HIGH" if productive >= 3 else "MEDIUM" if productive else "LOW",
            "HIGH" if redundant > productive else "LOW", "LOW" if any(a.status == "INVALID" for a in audits)
            else "MEDIUM" if any(a.status == "WEAKLY_SUPPORTED" for a in audits) else "HIGH",
            "HIGH" if independent else "LOW", "HIGH" if any(e.evidence_type == "EXECUTED_EVIDENCE" and e.passed for e in evidence) else "LOW",
            tuple(issues))
