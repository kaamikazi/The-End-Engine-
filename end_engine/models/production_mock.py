"""Offline production-agent research fixture. Operator responses depend on targets,
not an enforced operator sequence; the normal utility policy controls the run.
"""
from .base import ModelResponse
from .mock import MockProvider


PRODUCTION_TASK = "Design an autonomous software agent that can modify a production codebase while minimizing the risk of introducing regressions."
BASE = "Proposed agent constraints must be reviewed against production evidence. Passing unit tests alone does not authorize release."
ACTIONS = {
    "failure_mode": "Map concrete failure scenarios for stale checkout state, partial test coverage, dependency outages, and irreversible external side effects.",
    "alternatives": "Compare separated patch-generation and release workflows before granting write authority.",
    "downstream": "Use independently owned holdout scenarios, immutable audit records, and release-outcome metrics to resist test gaming.",
    "verification": "Specify auditable acceptance checks for isolation, regression detection, rollback drills, and explicit release approval.",
}


class ProductionAgentMockProvider(MockProvider):
    def metadata(self):
        return {"provider": "mock", "model": "production-agent-fixture-v2", "offline": True}

    def generate_structured(self, request):
        if request.purpose in self.scripted:
            return super().generate_structured(request)
        c, purpose = request.context, request.purpose
        if purpose == "initial_candidate":
            data = {"content": "Assume passing unit tests adequately represent production behavior. "
                    "The agent edits the production checkout directly, runs tests, and deploys when green.",
                    "known_strengths": ["Concrete initial workflow"], "confidence": None}
        elif purpose == "revision":
            previous = c["candidate"]["content"]
            content = BASE if "Assume passing" in previous else previous
            for change in c["revision_plan"]["changes"]:
                if change["action"] not in content:
                    content += " " + change["action"]
            data = {"content": content, "known_strengths": ["Explicit risk controls and evaluation boundaries"], "confidence": None}
        elif purpose == "critique":
            op = c["operator"]
            knowledge = c.get("cognitive_context") or {"claims": [], "assumptions": []}
            data = {"summary": "Inspect the concrete production-agent uncertainty.", "findings": []}
            finding_specs = {
                "ASSUMPTION": ("failure_mode", "Passing unit tests misses unrepresented production failures.", "Tests do not cover all production conditions."),
                "WHAT_BREAKS": ("alternatives", "Direct edits couple generation, validation, and release authority.", "The design needs a competing isolation and validation workflow."),
                "ALTERNATIVE": ("downstream", "Automation incentives can reward green tests while production outcomes degrade.", "A separated workflow alone does not prevent test gaming."),
                "SECOND_ORDER_EFFECT": ("verification", "Release gates lack auditable acceptance checks independent of the proposing agent.", "Independent criteria need observable pass conditions."),
            }
            if op in finding_specs:
                kind, description, evidence = finding_specs[op]
                existing = next((w for w in c["weaknesses"] if w["description"] == description), None)
                data["findings"] = [{"weakness_id": existing["id"] if existing else None, "type": kind,
                                     "severity": "high", "description": description, "evidence": evidence}]
            if op == "ASSUMPTION":
                data["assumption_updates"] = [{"id": a["assumption_id"], "status": "INVALIDATED",
                    "evidence": "Passing unit tests alone cannot establish coverage of unrepresented production behavior."}
                    for a in knowledge["assumptions"] if a["status"] == "UNTESTED"]
                data["claim_updates"] = [{"id": claim["claim_id"], "status": "CONTRADICTED",
                    "evidence": "The proposed test-to-production inference lacks a coverage argument."} for claim in knowledge["claims"]]
            if op == "WHAT_BREAKS":
                data["assumptions"] = [{"statement": "Rollback can recover all externally visible side effects.",
                    "risk": "MEDIUM", "status": "UNTESTED", "evidence": "External actions are outside a code rollback transaction."}]
                data["reframing"] = {"reframed_problem": "Design bounded patch proposal and independent release gating, with production regression risk as the objective.",
                    "reason": "The uncertainty concerns authority and validation boundaries as well as patch correctness.", "confidence": 0.88}
            if op == "SECOND_ORDER_EFFECT":
                data["assumption_updates"] = [{"id": a["assumption_id"], "status": "INVALIDATED",
                    "evidence": "Code rollback cannot undo emails or external payments; the plan requires explicit side-effect boundaries."}
                    for a in knowledge["assumptions"] if a["status"] == "UNTESTED"]
            if op in ("VERIFY", "EVIDENCE"):
                data["summary"] = "Check that acceptance criteria and independent authority are explicit in the proposal. No real tests were executed."
                data["claim_updates"] = [{"id": claim["claim_id"], "status": "SUPPORTED",
                    "evidence": "The candidate explicitly specifies independent review and auditable acceptance checks; fixture judgment of proposal content only."}
                    for claim in knowledge["claims"] if claim["evidence_status"] == "UNVERIFIED"
                    and "independently reviewed" in c["candidate"]["content"]]
            if op == "VERIFY":
                data["findings"] = [{"weakness_id": next((w["id"] for w in c["weaknesses"] if w["type"] == "verification"), None),
                    "type": "verification", "severity": "high", "description": finding_specs["SECOND_ORDER_EFFECT"][1],
                    "evidence": "Specify the exact release-gate checklist before accepting this proposal."}]
        elif purpose == "revision_plan":
            changes = []
            selected = c["critique"]["operator"]
            target_kind = {"ASSUMPTION": "failure_mode", "WHAT_BREAKS": "failure_mode",
                           "ALTERNATIVE": "alternatives", "SECOND_ORDER_EFFECT": "downstream", "VERIFY": "verification"}.get(selected)
            for w in c["weaknesses"]:
                if w["status"] == "open" and w["type"] == target_kind:
                    action = "Record the limits of unit-test coverage and require explicit production failure scenarios." if selected == "ASSUMPTION" else ACTIONS[w["type"]]
                    changes.append({"targets": [w["id"]], "action": action,
                                    "expected_effect": "Address this identified uncertainty with a checkable control."})
            if c.get("synthesis"):
                for item in c["synthesis"]["adopt"]:
                    changes.append({"targets": [], "action": item["element"],
                                    "expected_effect": "Integrate this evaluated branch component into the proposal."})
            data = {"changes": changes}
        elif purpose == "verification":
            content = c["candidate"]["content"]
            score = min(0.98, 0.53 + 0.09*c["candidate"]["iteration"])
            updates = []
            for w in c["weaknesses"]:
                marker = "Use an isolated worktree" if w["type"] == "alternatives" else ACTIONS.get(w["type"], "UNIMPLEMENTED")
                if marker in content and w["status"] == "open":
                    updates.append({"id": w["id"], "status": "resolved", "reason": f"Proposal contains the corresponding explicit control: {marker}"})
            passed = ACTIONS["verification"] in content and "Use an isolated worktree" in content
            data = {"passed": passed, "score": score, "dimensions": {d: score for d in c["dimensions"]},
                    "remaining_issues": [] if passed else ["Production-agent design still needs independent failure and acceptance scrutiny."],
                    "weakness_updates": updates}
        elif purpose == "branch_generation":
            options = [
                {"hypothesis": "Direct patch workflow", "content": "Let the proposing agent edit the production checkout and run its own test suite. Fast but authority and validation are coupled."},
                {"hypothesis": "Isolated worktree workflow", "content": "Use an isolated worktree with narrow patch permissions, independently reviewed diffs, and reproducible validation."},
                {"hypothesis": "Staged patch with shadow validation", "content": "Validate staged patches with production-like shadow scenarios, independent holdouts, bounded canary release, and rollback drills."},
            ]
            data = {"branches": options[:c["max_branches"]]}
        elif purpose == "branch_evaluation":
            direct = c["branch"]["hypothesis"] == "Direct patch workflow"
            score = 0.35 if direct else 0.91
            data = {"scores": {d: (0.85 if d == "simplicity" and direct else score) for d in c["dimensions"]},
                    "strengths": ["Fast edit turnaround"] if direct else [c["branch"]["content"]],
                    "weaknesses": ["Coupled authority permits unreviewed regressions"] if direct else ["Requires independently maintained validation scenarios"],
                    "recommendation": "REJECT" if direct else "MERGE_COMPONENTS"}
        elif purpose == "synthesis":
            data = {"source_branches": [b["branch_id"] for b in c["branches"]], "adopt": [], "reject": []}
            for b in c["branches"]:
                if b["status"] == "PROMISING":
                    data["adopt"].append({"branch": b["branch_id"], "element": b["content"]})
                else:
                    data["reject"].append({"branch": b["branch_id"], "element": b["hypothesis"],
                                           "reason": "Generation and release authority remain coupled."})
        else:
            return super().generate_structured(request)
        return ModelResponse(data)
