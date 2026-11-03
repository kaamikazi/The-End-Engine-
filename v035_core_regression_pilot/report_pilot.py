"""Derived diagnostics of this pilot only. No historical record is rescored/written."""
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
import shutil

OUT=Path(__file__).resolve().parent
CONDITIONS=("DIRECT","FULL_END_STRUCTURED","FULL_END_NATIVE")
TASKS=("BA-001","BA-002","BA-008","BA-009")


def load(path):return json.loads(Path(path).read_text(encoding="utf-8"))


def metrics(record,evaluation,trajectory=None):
    calls=record["calls"];purposes=Counter(c["purpose"] for c in calls)
    judge=sum(purposes[p] for p in ("judgment","comparison","adversarial_judgment","adversarial_tests","blinded_external_judgment"))
    verifier=purposes["verification"]
    end=record.get("end") or {};events=(trajectory or {}).get("protocol_events",[])
    actions=Counter(e["action"] for e in events)
    discarded=sum(len(e.get("discarded",[]))+len(e.get("rejected",[])) for e in events
                  if e["action"] in ("invalid_elements_discarded","invalid_targets_discarded","invalid_updates_rejected"))
    grounding=(trajectory or {}).get("judge_groundings",[])
    all_issues=[]
    for j in ((trajectory or {}).get("judgments",[])+(trajectory or {}).get("adversarial_judgments",[])):
        for name in ("fatal_issues","major_issues","minor_issues"):
            for issue in j[name]:all_issues.append({"judgment_id":j["judgment_id"],"candidate_id":j["candidate_id"],"kind":name,**issue})
    decisive=sum(i.get("decisive",True) for i in all_issues)
    final=evaluation["final"];c0=evaluation["candidates"].get("C0")
    result={"run_id":record["run_id"],"task":record["task_id"],"condition":record["condition"],
        "external_score":final["score"],"passed":final["passed"],"format_ok":final["format_ok"],"wall_seconds":record["cost"]["wall_ms"]/1000,
        "total_model_calls":record["cost"]["calls"],"generator_calls":len(calls)-judge-verifier,"judge_calls":judge,"verifier_calls":verifier,
        "protocol_repair_calls":sum(c.get("protocol_repair_call",False) for c in calls),
        "transport_retry_calls":sum(c["attempt"]>1 for c in calls),"tokens":record["cost"]["total_tokens"],
        "prompt_tokens":record["cost"]["prompt_tokens"],"output_tokens":record["cost"]["completion_tokens"],
        "end_cycles":end.get("iterations",0),"stop_reason":end.get("termination"),
        "external_blocker":end.get("termination")=="EXTERNAL_BLOCKER","model_protocol_failure":end.get("termination")=="MODEL_PROTOCOL_FAILURE",
        "execution_error":bool(record.get("error")),"repair_attempts":actions["repair_requested"],"repair_successes":actions["repaired"],
        "discarded_protocol_elements":discarded,"rollback_count":len(end.get("rollback_events",[])),"quality_gate":end.get("quality_gate"),
        "c0_score":c0 and c0["score"],"c0_format_ok":c0 and c0["format_ok"],"c0_chars":c0 and c0["answer_chars"],
        "final_chars":final["answer_chars"],"truncated_calls":record["cost"]["truncated_text_answers"],
        "internal_leakage":sum(bool(c.get("internal_leakage")) for c in (trajectory or {}).get("engine_checks",[])),
        "grounding_incidents":len(grounding),"decisive_judge_findings":decisive,"nondecisive_judge_findings":len(all_issues)-decisive,
        "unsupported_claim_count":final["counters"]["unsupported_claim_count"],
        "overthinking_signals":((evaluation.get("analysis") or {}).get("overthinking",[])),
        "candidate_progression":evaluation.get("candidates",{}),"operator_sequence":[s["data"]["operator"] for s in
             (trajectory or {}).get("steps",[]) if s["type"]=="operator_selection"],"judge_findings":all_issues,
        "grounding_records":grounding,"protocol_events":events,"error_records":record.get("error") or end.get("errors",[])}
    assert result["generator_calls"]+result["judge_calls"]+result["verifier_calls"]==result["total_model_calls"]
    return result


def summarize():
    from .run_pilot import write_json
    if not (OUT/"manifest.json").exists():return
    manifest=load(OUT/"manifest.json");rows=[];incomplete_evaluations=[]
    for path in sorted((OUT/"trials").glob("*.json")):
        record=load(path);ev_path=OUT/"evaluations"/path.name
        if not ev_path.exists():incomplete_evaluations.append(record["run_id"]);continue
        evaluation=load(ev_path)
        trajectory=load(OUT/"trajectories"/record["end"]["trajectory_file"]) if record.get("end") else None
        row=metrics(record,evaluation,trajectory);rows.append(row)
        write_json(OUT/"diagnostics"/path.name,row)
        if not row["passed"] or row["model_protocol_failure"] or row["external_blocker"] or row["grounding_incidents"] or row["overthinking_signals"]:
            archive=OUT/"failures"/record["run_id"];archive.mkdir(parents=True,exist_ok=True)
            for source,name in ((path,"trial.json"),(ev_path,"evaluation.json"),(OUT/"diagnostics"/path.name,"diagnostics.json")):
                destination=archive/name
                if not destination.exists():shutil.copyfile(source,destination)
            write_json(archive/"reference.json",{"trajectory_file":record.get("end",{}).get("trajectory_file") if record.get("end") else None,
                       "wire_directory":"../../wire/"+record["run_id"]})
    fields=["run_id","task","condition","external_score","passed","format_ok","wall_seconds","total_model_calls",
            "generator_calls","judge_calls","verifier_calls","protocol_repair_calls","transport_retry_calls","tokens",
            "prompt_tokens","output_tokens","end_cycles","stop_reason","external_blocker","model_protocol_failure",
            "repair_attempts","repair_successes","discarded_protocol_elements","rollback_count","quality_gate","c0_score",
            "c0_format_ok","c0_chars","final_chars","truncated_calls","internal_leakage","grounding_incidents",
            "decisive_judge_findings","nondecisive_judge_findings","unsupported_claim_count"]
    with (OUT/"results.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction="ignore");writer.writeheader();writer.writerows(rows)
    aggregate={}
    for condition in CONDITIONS:
        group=[r for r in rows if r["condition"]==condition]
        aggregate[condition]={"runs":len(group),"passed":sum(r["passed"] for r in group),
            "mean_external_score":sum(r["external_score"] for r in group)/len(group) if group else None,
            "wall_seconds":sum(r["wall_seconds"] for r in group),"model_calls":sum(r["total_model_calls"] for r in group),
            "tokens":None if any(r["tokens"] is None for r in group) else sum(r["tokens"] for r in group),
            "protocol_failures":sum(r["model_protocol_failure"] for r in group),"external_blockers":sum(r["external_blocker"] for r in group)}
    summary={"experiment":manifest["experiment"],"status":manifest["status"],"planned":12,"completed":len(rows),
        "incomplete_evaluations":incomplete_evaluations,"failed_executions":sum(r["execution_error"] or r["external_blocker"] or r["model_protocol_failure"] for r in rows),
        "failed_external_outcomes":sum(not r["passed"] for r in rows),"total_wall_seconds":sum(r["wall_seconds"] for r in rows),
        "total_model_calls":sum(r["total_model_calls"] for r in rows),"total_tokens":None if any(r["tokens"] is None for r in rows)
        else sum(r["tokens"] for r in rows),"aggregates":aggregate,"runs":rows,"jev_calls":0,"cloud_calls":0,
        "limitations":["Four tasks, one trial per condition; descriptive mechanism diagnostic only", "FULL_END capped at three cycles; not equivalent to uncapped Alpha/Beta", "Ollama server version differs from historical Alpha", "Same local model generates and judges; external evaluator is ground truth only for its encoded checks"]}
    write_json(OUT/"summary.json",summary)
    lines=["# v0.3.5 Core Regression Pilot — diagnostic report", "", "## 1. Purpose", "",
        "Test the concrete protocol/grounding/false-premise/consensus failures, without changing END or treating this as Benchmark Beta.",
        "", "## 2. Experimental limitations", "", *["- "+s for s in summary["limitations"]],
        "", "## 3. Environment and identities", "", "```json",json.dumps({k:manifest[k] for k in ("engine","model_identity","model_settings","task_hashes","evaluator_sha256")},indent=2),"```",
        "", "## 4. Exact 12-run matrix", "", "| Task | Seeded condition order |", "|---|---|"]
    for task in TASKS:lines.append("| "+task+" | "+" → ".join(p["condition"] for p in manifest["plan"] if p["task_id"]==task)+" |")
    lines.extend(["", "## 5. Aggregate results", "",f"Status: **{manifest['status']}**; completed {len(rows)}/12; failed executions {summary['failed_executions']}; external failures {summary['failed_external_outcomes']}.",
                  "", "| Task | Condition | Score | Pass | Format | Cycles | Gate | Stop |", "|---|---|---:|---|---|---:|---|---|"])
    by_run={r["run_id"]:r for r in rows}
    for p in manifest["plan"]:
        r=by_run.get(p["run_id"])
        lines.append(f"| {p['task_id']} | {p['condition']} | "+(f"{r['external_score']:.4f} | {r['passed']} | {r['format_ok']} | {r['end_cycles']} | {r['quality_gate']} | {r['stop_reason']} |" if r else "— | NOT RUN | — | — | — | — |"))
    lines.extend(["", "## 6. Runtime and model-call cost", "",f"Completed-run Engine/inference wall: {summary['total_wall_seconds']/3600:.3f} hours; {summary['total_model_calls']} actual Ollama attempts; tokens {summary['total_tokens']}. Monetary cost/energy not measured.",
        "", "Generator/judge/verifier counts and protocol-vs-transport retries are separated in results.csv. Protocol repair calls are a subset, not added twice.",
        "", "Runtime projections (fixed formula in manifest):", "```json",json.dumps(manifest["runtime_projections"],indent=2),"```"])
    sections=((7,"BA-001 protocol recovery","BA-001"),(8,"BA-002 grounded judgment","BA-002"),
              (9,"BA-008 false-premise behavior","BA-008"),(10,"BA-009 consensus/verification behavior","BA-009"))
    for number,title,task in sections:
        lines.extend(["",f"## {number}. {title}","", "| Condition | Repairs requested/succeeded | Discarded | Grounding incidents | Outcome |", "|---|---:|---:|---:|---|"])
        for r in rows:
            if r["task"]==task:lines.append(f"| {r['condition']} | {r['repair_attempts']}/{r['repair_successes']} | {r['discarded_protocol_elements']} | {r['grounding_incidents']} | {r['external_score']} / {r['stop_reason']} |")
        lines.append("\nPrimary mechanism verdict: see manual review and final interpretation below; score alone is not a mechanism verdict.")
    lines.extend(["", "## 11. Structured vs native C0", "", "| Task | Condition | C0 or DIRECT score | Format | Chars |", "|---|---|---:|---|---:|"])
    for r in rows:
        lines.append(f"| {r['task']} | {r['condition']} | {r['external_score'] if r['condition']=='DIRECT' else r['c0_score']} | {r['format_ok'] if r['condition']=='DIRECT' else r['c0_format_ok']} | {r['final_chars'] if r['condition']=='DIRECT' else r['c0_chars']} |")
    lines.extend(["", "## 12. Candidate progression", ""])
    for r in rows:
        if r["condition"]!="DIRECT":lines.append(f"- {r['run_id']}: "+" → ".join(f"{c}={s['score']}/{s['passed']}" for c,s in r["candidate_progression"].items()))
    lines.extend(["", "## 13. Judge grounding incidents", "",f"Nondecisive incidents: {sum(r['grounding_incidents'] for r in rows)}. All annotated issues are preserved in diagnostics/*.json; inspect provenance and quoted candidate/task spans.",
        "", "## 14. Rollback / overthinking", ""])
    for r in rows:
        if r["condition"]!="DIRECT":lines.append(f"- {r['run_id']}: rollbacks={r['rollback_count']}; operators={r['operator_sequence']}; overthinking={r['overthinking_signals']}")
    lines.extend(["", "## 15. Manual review of all FULL_END runs", "", "See MANUAL_REVIEW.md. All eight require review; incomplete/unexecuted runs remain explicitly unreviewed.",
        "", "## 16. Failure archive", "", "failures/ retains immutable trial/evaluation/diagnostic copies and trajectory references. Full observable model request/response artifacts are in wire/; interrupted attempts are preserved separately.",
        "", "## 17. Historical Alpha comparison", "", "Alpha records remain read-only and are not rescored. Historical references and capped pilot findings must be described separately; neither three-cycle capping, seed nor server-version differences support a final superiority claim.",
        "", "## 18. What v0.3.5 appears to have fixed", "", "Pending manual interpretation; no aggregate pass-rate substitution.",
        "", "## 19. What remains broken", "", "Pending manual interpretation. Preserve failure cases and cost without external benefit.",
        "", "## 20. Recommendation", "", "Pending the complete/manual diagnostic review; no automatic full Beta launch."])
    if (OUT/"INTERPRETATION.md").exists():lines.extend(["", "## Final manual interpretation", "",(OUT/"INTERPRETATION.md").read_text(encoding="utf-8")])
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return summary
