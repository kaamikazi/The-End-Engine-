"""Twelve-run, local-only, resumable v0.3.5 diagnostic pilot.

CLI: python -B -m v035_core_regression_pilot.run_pilot preflight|live|summarize
No Engine, prior benchmark, task, prompt, setting or evaluator is modified.
"""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sys
import time
import traceback
import urllib.request

from end_engine import EngineConfig
from .bench.conditions import EndSettings, run_direct, run_full_end
from .bench.providers import CallLog, ModelSettings, OllamaModel
from .bench.upstream_runner import evaluate_run, trial_seed


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
TASKS = ("BA-001", "BA-002", "BA-008", "BA-009")
CONDITIONS = ("DIRECT", "FULL_END_STRUCTURED", "FULL_END_NATIVE")
SEED = 20261005
LIMIT_SECONDS = 6*3600
EXPECTED_DIGEST = "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7"
SETTINGS = ModelSettings("qwen3:4b")


class InfrastructureDefect(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
    if exclusive:
        with path.open("x",encoding="utf-8",newline="\n") as stream:
            stream.write(text);stream.flush();os.fsync(stream.fileno())
    else:
        temp=path.with_suffix(path.suffix+".tmp")
        with temp.open("w",encoding="utf-8",newline="\n") as stream:
            stream.write(text);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)


def append(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(data,ensure_ascii=False,allow_nan=False)+"\n");stream.flush();os.fsync(stream.fileno())


def execution_plan():
    rng=random.Random(SEED);plan=[]
    for task in TASKS:
        order=list(CONDITIONS);rng.shuffle(order)
        for condition in order:
            plan.append({"run_id":f"{task}.T1.{condition}","task_id":task,"trial":1,"condition":condition,"position":len(plan)+1})
    return plan


def local_json(path,payload=None,timeout=10):
    if path not in ("/api/tags","/api/version","/api/generate"):
        raise InfrastructureDefect("Only declared loopback Ollama endpoints are allowed")
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request=urllib.request.Request("http://127.0.0.1:11434"+path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type":"application/json"} if payload is not None else {})
    with opener.open(request,timeout=timeout) as result:
        return json.loads(result.read().decode("utf-8"))


def model_identity():
    models=local_json("/api/tags")["models"]
    model=next((m for m in models if m.get("name")==SETTINGS.model),None)
    if model is None or model.get("digest")!=EXPECTED_DIGEST:
        raise InfrastructureDefect("Required Alpha model/digest is not installed locally; no pull/fallback allowed")
    return {**model,"server_version":local_json("/api/version")["version"]}


def frozen_hashes():
    names=["run_pilot.py","report_pilot.py","tests.py"]
    return {p.relative_to(OUT).as_posix():sha(p) for p in
            [*(OUT/n for n in names),*sorted((OUT/"bench").glob("*.py")),*sorted((OUT/"tasks").glob("*.json"))]}


def assert_unchanged(manifest):
    for relative,expected in load(OUT/"preflight/engine-source-before.json").items():
        if sha(ROOT/relative)!=expected:raise InfrastructureDefect("Engine source changed during the pilot: "+relative)
    for relative,expected in manifest["pilot_source_hashes"].items():
        if sha(OUT/relative)!=expected:raise InfrastructureDefect("Frozen pilot code/task changed: "+relative)
    for name,expected in manifest["task_hashes"].items():
        if sha(ROOT/"benchmark_alpha/tasks"/(name+".json"))!=expected:
            raise InfrastructureDefect("Historical task changed")
    if sha(ROOT/"benchmark_alpha/bench/evaluators.py")!=manifest["evaluator_sha256"]:
        raise InfrastructureDefect("Historical evaluator changed")


def preflight():
    path=OUT/"manifest.json"
    if path.exists():
        manifest=load(path);assert_unchanged(manifest);return manifest
    engine=load(OUT/"preflight/engine-identity.json")
    if engine["version"]!="0.3.5" or engine["offline_tests"]["failures"] or engine["offline_tests"]["errors"]:
        raise InfrastructureDefect("Engine version/offline preflight failed")
    task_hashes={task:sha(OUT/"tasks"/(task+".json")) for task in TASKS}
    assert all(v==sha(ROOT/"benchmark_alpha/tasks"/(k+".json")) for k,v in task_hashes.items())
    evaluator=sha(OUT/"bench/evaluators.py")
    assert evaluator==sha(ROOT/"benchmark_alpha/bench/evaluators.py")
    identity=model_identity()
    configs={name:asdict(EndSettings(full_max_cycles=3).full_config(OUT/"trajectories",generation))
             for name,generation in (("FULL_END_STRUCTURED","structured"),("FULL_END_NATIVE","native"))}
    a=dict(configs["FULL_END_STRUCTURED"]);b=dict(configs["FULL_END_NATIVE"]);a.pop("candidate_generation");b.pop("candidate_generation")
    assert a==b and a["decision"]["provider"]=="baseline" and a["protocol_repair_attempts"]==1
    plan=execution_plan();assert len(plan)==12 and len({p["run_id"] for p in plan})==12
    manifest={"experiment":"v0.3.5 Core Regression Pilot","status":"PREFLIGHT_COMPLETE","diagnostic_only":True,
        "not_benchmark_beta":True,"created_at":now(),"engine":engine,"model_identity":identity,
        "historical_ollama_version":"0.35.0","ollama_version_changed":identity["server_version"]!="0.35.0",
        "model_settings":asdict(SETTINGS),"task_ids":list(TASKS),"task_hashes":task_hashes,
        "evaluator_sha256":evaluator,"evaluator_source":"byte-identical copy of benchmark_alpha/bench/evaluators.py",
        "transport_source":"byte-identical copy of benchmark_beta/bench/providers.py (v0.3.5 error taxonomy)",
        "conditions":list(CONDITIONS),"trials":1,"planned_runs":12,"randomization_seed":SEED,
        "plan":plan,"end_configs":configs,"full_end_max_cycles":3,"decision_provider":"baseline",
        "jev_calls_allowed":0,"cloud_inference_allowed":False,"pilot_source_hashes":frozen_hashes(),
        "runtime_guard":{"threshold_seconds":LIMIT_SECONDS,"after_first_FULL_END":True,
            "formula":"elapsed completed runs + mean completed FULL_END wall * remaining FULL_END + mean DIRECT wall * remaining DIRECT; if no DIRECT observed, use its 900s timeout upper bound"},
        "runtime_projections":[],"completed_runs":[],"sessions":[]}
    write_json(path,manifest,exclusive=True)
    return manifest


def projection(records,plan):
    complete={r["run_id"] for r in records}
    full=[r["cost"]["wall_ms"]/1000 for r in records if r["condition"].startswith("FULL_END")]
    direct=[r["cost"]["wall_ms"]/1000 for r in records if r["condition"]=="DIRECT"]
    if not full:return None
    remaining=[p for p in plan if p["run_id"] not in complete]
    direct_mean=sum(direct)/len(direct) if direct else SETTINGS.timeout_seconds
    full_mean=sum(full)/len(full)
    elapsed=sum(r["cost"]["wall_ms"]/1000 for r in records)
    total=elapsed+sum(full_mean if p["condition"].startswith("FULL_END") else direct_mean for p in remaining)
    return {"recorded_at":now(),"completed_runs":len(records),"completed_wall_seconds":elapsed,
        "full_runs_observed":len(full),"mean_FULL_END_seconds":full_mean,"DIRECT_estimate_seconds":direct_mean,
        "DIRECT_estimate_basis":"observed mean" if direct else "900s timeout upper bound",
        "projected_total_seconds":total,"projected_total_hours":total/3600,"threshold_exceeded":total>LIMIT_SECONDS}


class DurableCallLog(CallLog):
    def __init__(self,run_id):
        super().__init__();self.run_id=run_id;self.request=None

    def add(self,**entry):
        request=self.request
        entry["protocol_repair_call"]=bool(request and (request.context.get("protocol_repair") or
            "Repair the previous structured output" in request.prompt))
        entry["wire_file"]=f"wire/{self.run_id}/{len(self.entries)+1:04d}.json"
        item=super().add(**entry)
        append(OUT/"call_logs"/(self.run_id+".jsonl"),item)
        print(json.dumps({"event":"call_completed","run_id":self.run_id,"call":item["seq"],
                          "purpose":item["purpose"],"status":item["status"],"seconds":item["latency_ms"]/1000}),flush=True)
        return item


class PilotModel(OllamaModel):
    def _call(self,request,*,structured):
        self.log.request=request
        return super()._call(request,structured=structured)


class LocalTransport:
    def __init__(self,run_id,log):self.run_id,self.log=run_id,log

    def __call__(self,payload):
        expected={"temperature":.7,"top_p":.8,"num_predict":4096,"num_ctx":8192}
        if (payload["model"]!=SETTINGS.model or payload.get("think") is not False or
            any(payload["options"].get(k)!=v for k,v in expected.items())):
            raise InfrastructureDefect("Frozen local model settings violated")
        seq=len(self.log.entries)+1
        status={"state":"MODEL_CALL","run_id":self.run_id,"call":seq,"purpose":self.log.request.purpose,
                "started_at":now(),"pid":os.getpid()}
        write_json(OUT/"status.json",status)
        path=OUT/"wire"/self.run_id/f"{seq:04d}.json"
        start=time.perf_counter();data=None;error=None
        try:
            data=local_json("/api/generate",payload,SETTINGS.timeout_seconds)
            return data
        except Exception as exc:
            error={"type":type(exc).__name__,"message":str(exc)[:1000]}
            raise
        finally:
            # Observable answer/stats only; omit irrelevant token-context arrays and separate hidden thinking fields.
            retained={k:v for k,v in (data or {}).items() if k not in ("context","thinking")}
            write_json(path,{"run_id":self.run_id,"seq":seq,"purpose":self.log.request.purpose,
                "requested_at":status["started_at"],"completed_at":now(),"endpoint":"http://127.0.0.1:11434/api/generate",
                "payload":payload,"response":retained,"error":error,
                "latency_ms":round((time.perf_counter()-start)*1000,3)},exclusive=True)


def records():
    return [load(p) for p in sorted((OUT/"trials").glob("*.json"))] if (OUT/"trials").exists() else []


def archive_incomplete(run_id):
    paths=[OUT/"wire"/run_id,OUT/"call_logs"/(run_id+".jsonl")]
    if not any(p.exists() for p in paths):return
    destination=OUT/"incomplete_attempts"/run_id/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    destination.mkdir(parents=True)
    for path in paths:
        if path.exists():
            target=destination/path.name
            if not path.resolve().is_relative_to(OUT.resolve()) or not target.resolve().is_relative_to(OUT.resolve()):
                raise InfrastructureDefect("Unsafe incomplete-artifact move")
            shutil.move(str(path),str(target))


def live():
    # Process-local only. No secret is read, printed or sent to the loopback transport.
    for name in ("TYPESAFE_API_KEY","GEMINI_API_KEY","GOOGLE_API_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY"):
        os.environ.pop(name,None)
    manifest=preflight();assert_unchanged(manifest)
    if model_identity()["digest"]!=manifest["model_identity"]["digest"]:
        raise InfrastructureDefect("Model identity changed")
    from .report_pilot import summarize
    session={"started_at":now(),"completed":0,"skipped_existing":0};manifest["sessions"].append(session)
    manifest["status"]="RUNNING";write_json(OUT/"manifest.json",manifest)
    end_settings=EndSettings(full_max_cycles=3)
    for step in manifest["plan"]:
        run_id=step["run_id"];trial_path=OUT/"trials"/(run_id+".json")
        if trial_path.exists():session["skipped_existing"]+=1;continue
        assert_unchanged(manifest)
        prior=records();estimate=projection(prior,manifest["plan"])
        if estimate and estimate["threshold_exceeded"]:
            manifest["runtime_projections"].append(estimate);manifest["status"]="STOPPED_RUNTIME_GUARD"
            manifest["stop_reason"]="Observed total projection exceeds six hours; no additional expensive run launched"
            write_json(OUT/"manifest.json",manifest);break
        archive_incomplete(run_id)
        task=load(OUT/"tasks"/(step["task_id"]+".json"));log=DurableCallLog(run_id)
        model=PilotModel(SETTINGS,manifest["model_identity"],log,trial_seed=trial_seed(SEED,step["task_id"],1),
                         transport=LocalTransport(run_id,log))
        start=time.perf_counter();started=now();error=None
        print(json.dumps({"event":"run_started",**step}),flush=True)
        try:
            output=(run_direct(task,model) if step["condition"]=="DIRECT" else
                    run_full_end(task,model,OUT/"trajectories",end_settings,
                                 "native" if step["condition"]=="FULL_END_NATIVE" else "structured"))
        except Exception as exc:
            output={"answer":"","stages":{}}
            error={"type":type(exc).__name__,"message":str(exc)[:1500],"traceback":traceback.format_exc()}
        wall=round((time.perf_counter()-start)*1000,3)
        cost={**log.totals(),"wall_ms":wall,"end_cycles":(output.get("end") or {}).get("iterations"),
              "branch_count":(output.get("end") or {}).get("branch_count"),"tool_check_calls":0}
        record={**step,"trial_id":step["task_id"]+".T1","data_origin":"LIVE_LOCAL_MODEL_CAPPED_DIAGNOSTIC",
            "started_at":started,"ended_at":now(),"answer":output["answer"],"stages":output["stages"],
            "end":output.get("end"),"error":error,"cost":cost,"calls":log.entries,"model":model.metadata()}
        write_json(trial_path,record,exclusive=True)  # Completed inference preserved BEFORE derived evaluation.
        try:
            evaluation=evaluate_run(task,record,OUT)
            write_json(OUT/"evaluations"/(run_id+".json"),evaluation,exclusive=True)
            if record.get("end"):
                trajectory=load(OUT/"trajectories"/record["end"]["trajectory_file"])
                cfg=trajectory["configuration"]
                if cfg["decision"]["provider"]!="baseline" or trajectory.get("decision_summary",{}).get("calls",0):
                    raise InfrastructureDefect("Decision provider activated unexpectedly")
                if (record["end"]["iterations"]>3 or cfg["overrides"]["max_cycles"]!=3 or
                        cfg["protocol_repair_attempts"]!=1):raise InfrastructureDefect("END cap/config violated")
        except Exception as exc:
            manifest["status"]="STOPPED_INFRASTRUCTURE_DEFECT";manifest["stop_reason"]=str(exc)
            write_json(OUT/"infrastructure_failure.json",{"run_id":run_id,"error":str(exc),"traceback":traceback.format_exc()})
            write_json(OUT/"manifest.json",manifest);break
        manifest["completed_runs"].append(run_id);session["completed"]+=1
        manifest["last_completed_at"]=now()
        current=projection(records(),manifest["plan"])
        if current:
            manifest["runtime_projections"].append(current)
            print(json.dumps({"event":"runtime_projection",**current}),flush=True)
        if current and current["threshold_exceeded"] and len(records())<12:
            manifest["status"]="STOPPED_RUNTIME_GUARD";manifest["stop_reason"]="Observed projection exceeds six hours"
        write_json(OUT/"manifest.json",manifest)
        summarize()
        print(json.dumps({"event":"run_completed","run_id":run_id,"score":evaluation["final"]["score"],
            "passed":evaluation["final"]["passed"],"seconds":wall/1000,"calls":cost["calls"],"error":error}),flush=True)
        if manifest["status"]=="STOPPED_RUNTIME_GUARD":break
    if len(records())==12 and not manifest["status"].startswith("STOPPED"):
        manifest["status"]="COMPLETED"
    session["ended_at"]=now();manifest["ended_at"]=now();write_json(OUT/"manifest.json",manifest)
    write_json(OUT/"status.json",{"state":manifest["status"],"completed":len(records()),"pid":os.getpid(),"ended_at":now()})
    summarize()
    return manifest


def main():
    os.environ["PYTHONDONTWRITEBYTECODE"]="1"
    command=sys.argv[1] if len(sys.argv)>1 else "preflight"
    if command=="preflight":
        manifest=preflight();print(json.dumps({"status":manifest["status"],"plan":manifest["plan"],
            "task_hashes":manifest["task_hashes"],"evaluator_sha256":manifest["evaluator_sha256"],
            "model_identity":manifest["model_identity"],"engine":manifest["engine"]},indent=2))
    elif command=="live":
        # OS lock releases on crash; prevents a second process from launching duplicate runs.
        import msvcrt
        with (OUT/"pilot.lock").open("a+b") as lock:
            if lock.seek(0,2)==0:lock.write(b"0");lock.flush()
            lock.seek(0)
            try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:raise SystemExit("Another pilot process holds the lock; no duplicate inference launched")
            try:live()
            finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    elif command=="summarize":
        from .report_pilot import summarize
        summarize()
    else:raise SystemExit("Use preflight, live or summarize")


if __name__=="__main__":main()
