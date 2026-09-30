"""OFFLINE_REASSESSMENT of the two preserved Antigravity smokes with the current Engine integrity logic.

Read-only: the Harness trajectories are opened for reading and hashed; nothing under the Harness is written. No model is
called. Recorded model outputs (candidates, judgments) are replayed through the real judge parser; recorded executed
evidence is used as recorded. Everything derived here is labelled OFFLINE_REASSESSMENT.

Reconstructed inputs (not recorded explicitly by the historical Engine versions, derived from step order):
  * which claim-status updates the Engine wrote (a claim_status_change immediately following the claim_validation of
    the same claim and status);
  * the claim, weakness and assumption state at each evaluation (latest recorded state before it);
  * the recorded run did not persist the live gate inputs (cognitive state object, dimension floors), so the gate is
    DERIVED from the recorded decision: integrity only adds uncertainties, which the gate evaluates after every
    REVISE/REJECT/BLOCKED return, so an ACCEPT_* decision gains them and any other decision is unaffected by them.
Usage: python -B validation_v034/offline_reassessment.py <output.json>"""
import hashlib
import json
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE))
from end_engine.core.state import Candidate, to_data  # noqa: E402
from end_engine.cognition.state import Claim, EvidenceStatus  # noqa: E402
from end_engine.quality.audits import ClaimValidator, ResolutionAuditor  # noqa: E402
from end_engine.quality.integrity import EvidenceIndex, EvidenceIntegrity, identical_content_findings  # noqa: E402
from end_engine.quality.judges import AdversarialJudge, CandidateJudge  # noqa: E402
from end_engine.quality.mock import MockJudgeProvider  # noqa: E402
from end_engine.quality.providers import _JudgeBridge  # noqa: E402
from end_engine.quality.state import EvidenceArtifact  # noqa: E402

HARNESS = Path(r"E:\The End Harness\output")
SMOKES = {
    "71532008": HARNESS / "antigravity-smoke/71532008-8e55-49f4-af8f-3a1086ae9f47/runs/0b4b326c-1bf5-4337-bb47-1f254880b5ca",
    "8b553c71": HARNESS / "antigravity-smoke-v032/8b553c71-30d1-41b5-9aa4-9ca917ac6a3b/runs/6af3c3b0-5338-442a-8911-11d3cd17a726",
}
LABEL = "OFFLINE_REASSESSMENT"


def replay_judgment(recorded, task, candidate, claims, evidence):
    raw = {k: recorded[k] for k in ("verdict", "dimensions", "fatal_issues", "major_issues", "minor_issues",
                                    "uncertainties", "evidence", "recommended_action")}
    purpose = "adversarial_judgment" if recorded["adversarial"] else "judgment"
    provider = _JudgeBridge(MockJudgeProvider(scripted={purpose: [raw]}), "offline-replay")
    kind = AdversarialJudge(provider) if recorded["adversarial"] else CandidateJudge(provider, recorded["judge_id"])
    return kind.judge(task, candidate, tuple(raw["dimensions"]), claims, evidence, recorded["judgment_id"])


def claim_obj(data):
    return Claim(data["claim_id"], data["text"], data["type"], data["source_candidate"], data.get("confidence"),
                 EvidenceStatus(data["evidence_status"]), data["evidence"])


def reassess(name, run):
    raw = (run / "trajectory.json").read_bytes()
    t = json.loads(raw)
    steps = t["steps"]
    kinds = [s["type"] for s in steps]
    # Reconstructed provenance: Engine-written claim updates follow the claim_validation that produced them.
    engine_evidence = set()
    for i, s in enumerate(steps):
        if s["type"] == "claim_status_change":
            j = i - 1
            while j >= 0 and steps[j]["type"] in ("claim_status_change", "claim_validation"):
                v = steps[j]["data"]
                if steps[j]["type"] == "claim_validation" and v["claim_id"] == s["data"]["after"]["claim_id"] \
                        and v["status"] == s["data"]["after"]["evidence_status"]:
                    engine_evidence.add((v["claim_id"], v["status"], s["data"]["after"]["evidence"]))
                    break
                j -= 1
    independent = t["judge_configuration"]["different_model_identity"]
    candidates = {c["candidate_id"]: c for c in t["candidates"]}
    gates = [s for s in steps if s["type"] == "quality_gate"]
    engine = json.loads((run.parent.parent / "manifest.json").read_text(encoding="utf-8"))["engine"]
    out = {"label": LABEL, "smoke": name, "trajectory": str(run / "trajectory.json"),
           "trajectory_sha256": hashlib.sha256(raw).hexdigest(),
           "engine_at_record": {"version": engine["version"], "source_sha256": engine["source_sha256"]},
           "claim_extractor_at_record": t["configuration"]["components"]["claim_extractor"],
           "different_model_identity": independent,
           "historical": {"termination": t["termination"], "final_candidate_id": t["final_candidate_id"],
                          "best_candidate_id": t["best_candidate_id"], "latest_candidate_id": t["latest_candidate_id"],
                          "quality_gate": t["scorecard"]["quality_gate"], "acceptance_label": t["acceptance_label"],
                          "gates": [g["data"] for g in gates]},
           "reconstructed_engine_written_claim_updates": sorted(map(list, engine_evidence)), "candidates": []}
    reports = []
    for g in gates:
        cid, gate_step = g["data"]["candidate_id"], g["step"]
        created = max(s["step"] for s in steps if s["type"] == "candidate" and s["data"]["candidate_id"] == cid)
        window = [s for s in steps if created <= s["step"] <= gate_step]
        first_eval = min(s["step"] for s in window if s["type"] in ("adversarial_test", "verifier_evidence", "judgment",
                                                                    "claim_validation"))
        prefix = [s for s in steps if s["step"] < gate_step]
        state = {}
        for s in steps:
            if s["step"] < first_eval and s["type"] in ("claim_discovered", "claim_status_change"):
                state[s["data"]["after"]["claim_id"]] = s["data"]["after"]
        validated = [s["data"]["claim_id"] for s in window if s["type"] == "claim_validation"]
        claims = tuple(claim_obj(state[c]) for c in validated)
        content = candidates[cid]["content"]
        candidate = Candidate(cid, candidates[cid]["parent_candidate_id"], candidates[cid]["iteration"], content,
                              candidates[cid]["created_at"])
        evidence = tuple(EvidenceArtifact(**{**s["data"], "targets": tuple(s["data"]["targets"])})
                         for s in window if s["type"] == "verifier_evidence")
        judgments = tuple(replay_judgment(s["data"], t["task"], candidate, claims, evidence)
                          for s in window if s["type"] in ("judgment", "adversarial_judgment"))
        validations = ClaimValidator().validate(claims, cid, evidence, content=content)
        recorded_validations = [{k: v for k, v in s["data"].items() if k != "candidate_id"}
                                for s in window if s["type"] == "claim_validation"]
        record = {"steps": prefix, "trajectory_id": t["trajectory_id"],
                  "candidates": [c for c in t["candidates"] if any(s["type"] == "candidate" and s["data"]["candidate_id"]
                                 == c["candidate_id"] for s in prefix)],
                  "revision_plans": [s["data"] for s in prefix if s["type"] == "revision_plan"],
                  "verifier_evidence": [s["data"] for s in prefix if s["type"] == "verifier_evidence"],
                  "adversarial_tests": [s["data"] for s in prefix if s["type"] == "adversarial_test"],
                  "judgments": [s["data"] for s in prefix if s["type"] == "judgment"],
                  "adversarial_judgments": [s["data"] for s in prefix if s["type"] == "adversarial_judgment"]}
        all_claims = {s["data"]["after"]["claim_id"]: s["data"]["after"] for s in prefix
                      if s["type"] in ("claim_discovered", "claim_status_change")}
        weaknesses = {w["id"] for s in prefix if s["type"] == "weakness_snapshot" for w in s["data"]}
        weaknesses |= {w for s in prefix if s["type"] == "judge_feedback" for w in s["data"]["weakness_ids"]}
        assumptions = {s["data"]["after"]["assumption_id"] for s in prefix
                       if s["type"] in ("assumption_discovered", "assumption_status_change")}
        audits = (*ResolutionAuditor().audit(record, candidate, evidence, judgments=judgments),
                  *ResolutionAuditor().audit(record, candidate, evidence, assumptions=True, judgments=judgments))
        recorded_audits = [s["data"] for s in window if s["type"] in ("resolution_audit", "assumption_audit")]
        by_step = {s["step"]: s["data"] for s in steps}
        transitions = tuple((f"{a.target_id}.{'evidence' if a.kind == 'assumption' else 'status_reason'}@step{a.transition_step}",
                             by_step.get(a.transition_step, {}).get("after", {}).get(
                                 "evidence" if a.kind == "assumption" else "status_reason", ""))
                            for a in audits if a.transition_step > created)
        index = EvidenceIndex(record, candidate, evidence=evidence, judgments=judgments,
                              claims=tuple(claim_obj(c) for c in all_claims.values()), weaknesses=tuple(weaknesses),
                              assumptions=tuple(assumptions))
        report = EvidenceIntegrity().assess(candidate, claims, evidence, judgments, validations, index, audits=audits,
                                            transitions=transitions, independent=independent,
                                            engine_evidence=engine_evidence)
        data = to_data(report)
        reports.append((gate_step, data))
        historical = g["data"]
        if historical["decision"] in ("ACCEPT_VERIFIED", "ACCEPT_PROVISIONALLY"):
            reasons = [] if historical["decision"] == "ACCEPT_VERIFIED" else list(historical["reasons"])
            reasons = list(dict.fromkeys([*reasons, *report.uncertainties]))
            derived = {"decision": "ACCEPT_PROVISIONALLY" if reasons else "ACCEPT_VERIFIED",
                       "reasons": reasons or list(historical["reasons"]), "derivation": "historical decision + integrity uncertainties"}
        else:
            derived = {"decision": historical["decision"], "reasons": historical["reasons"],
                       "derivation": "not affected by integrity (a return that precedes integrity uncertainties); "
                                     "other Engine changes since the recording are listed under audit_differences"}
        audit_differences = [{"target_id": a.target_id, "recorded": r["status"], "current_policy": a.status,
                              "current_reason": a.reason}
                             for a in audits for r in recorded_audits
                             if r["target_id"] == a.target_id and r["transition_step"] == a.transition_step and r["status"] != a.status]
        out["candidates"].append({
            "candidate_id": cid, "content_sha256": report.content_sha256, "evaluation_steps": [created, gate_step],
            "inputs": {"claims": [to_data(c) for c in claims], "evidence_ids": [e.artifact_id for e in evidence],
                       "judgment_ids": [j.judgment_id for j in judgments]},
            "validations_match_recorded": len(validations) == len(recorded_validations) and all(
                {k: v for k, v in to_data(x).items() if k != "out_of_scope_artifacts"} == r
                for x, r in zip(validations, recorded_validations)),
            "judge_unresolved_evidence": {j.judgment_id: list(j.unresolved_evidence) for j in judgments},
            "integrity": data, "historical_gate": historical, "derived_gate": derived,
            "audit_differences": audit_differences})
    final = t["final_candidate_id"]
    same = {c for c, x in candidates.items() if x["content"] == candidates[final]["content"]}
    valid_resolutions = [a for c in out["candidates"] if c["candidate_id"] in same for a in c["audit_differences"]
                         if a["current_policy"] == "VALID"]
    applicable, resolved_later, listed, uncertain = identical_content_findings(
        [(step, d) for step, d in reports if d["candidate_id"] in same], final, {})
    own = next(c for c in out["candidates"] if c["candidate_id"] == final)["derived_gate"]
    final_reasons = list(dict.fromkeys([*own["reasons"], *uncertain]))
    out["final"] = {"label": LABEL, "final_candidate_id": final, "identical_content_candidates": sorted(same),
                    "integrity_findings": {"applicable": applicable, "resolved_later": resolved_later},
                    "not_transferred": listed, "valid_resolutions_considered": valid_resolutions,
                    "reconciled_uncertainties_added": uncertain,
                    "derived_final_gate": (
                        {"decision": "BLOCKED", "acceptance_label": "INCOMPLETE",
                         "note": "termination EXTERNAL_BLOCKER is preserved; the final gate stays BLOCKED/INCOMPLETE and "
                                 "only lists added reasons", "added_reasons": uncertain}
                        if t["termination"]["reason"] == "EXTERNAL_BLOCKER" else
                        {"decision": "ACCEPT_PROVISIONALLY" if own["decision"] in ("ACCEPT_VERIFIED", "ACCEPT_PROVISIONALLY")
                         and (uncertain or own["decision"] == "ACCEPT_PROVISIONALLY") else own["decision"],
                         "reasons": final_reasons}),
                    "termination_preserved": t["termination"]}
    return out


if __name__ == "__main__":
    results = {"label": LABEL, "note": "Derived offline from recorded inputs; not a live run and not historical evidence.",
               "smokes": [reassess(name, run) for name, run in SMOKES.items()]}
    Path(sys.argv[1]).write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for smoke in results["smokes"]:
        print(f"== {LABEL} {smoke['smoke']} (trajectory sha256 {smoke['trajectory_sha256']})")
        print("  historical:", smoke["historical"]["termination"]["reason"], smoke["historical"]["quality_gate"],
              "final", smoke["historical"]["final_candidate_id"])
        for c in smoke["candidates"]:
            i = c["integrity"]
            print(f"  {c['candidate_id']}: validations match recorded={c['validations_match_recorded']}; "
                  f"claims={[(x['claim_id'], x['status'], x['status_source']) for x in i['claims']]}")
            print(f"     statements={[(s['source'], s['status']) for s in i['statements']]}")
            print(f"     references={[(r['source'], r['reference'], r['status']) for r in i['references']]}")
            print(f"     contradictions={[x['target'] for x in i['contradictions']]} uncertainties={i['uncertainties']}")
            print(f"     historical gate={c['historical_gate']['decision']} {c['historical_gate']['reasons']}")
            print(f"     derived gate={c['derived_gate']['decision']} {c['derived_gate']['reasons']}")
            if c["audit_differences"]:
                print(f"     audit differences (0.3.1 policy, not integrity)={c['audit_differences']}")
        f = smoke["final"]
        print("  final:", f["derived_final_gate"])
        print("  identical-content applicable:", f["integrity_findings"]["applicable"])
        print("  not transferred:", f["not_transferred"])
