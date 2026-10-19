"""Actual unchanged EndEngine and historical DIRECT/SELF_REFLECT via injection."""
import json
from pathlib import Path
from end_engine import EndEngine,EngineConfig
from end_engine.quality.providers import ModelJudgeProvider
from v0351_core_regression_pilot.bench.conditions import run_direct,run_self_reflect
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from ..native_end_bridge.bridge import NativeGateway,NativeBridge,RecordingTransport,verify_sources
from ..provider_protocol.canned import CannedScript
from ..provider_protocol.wire import SETTINGS,sha

def run_baseline(task,condition,directory,*,run_id='mock_run',mode='progress',global_attempts=136,shared_ledger=None):
    if condition not in ('DIRECT','SELF_REFLECT','FROZEN_CURRENT_END'):raise ValueError('Only existing baseline wiring authorized')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);verify_sources()
    if (directory/'MOCK_REPLAY.json').exists():raise FileExistsError('Completed mock record immutable; choose a new namespace')
    request=RunRequest(task['task_id'],task,SETTINGS.model,'UNOBSERVED_NO_MODEL_QUERIED',{'temperature':SETTINGS.temperature,'top_p':SETTINGS.top_p,'think':SETTINGS.think},None,SETTINGS.num_ctx,SETTINGS.num_predict,condition,36,400000,1800,run_id)
    ledger=shared_ledger if shared_ledger is not None else Ledger(directory/'budget.json',global_attempts=global_attempts);transport=RecordingTransport(CannedScript(mode));gateway=NativeGateway(request,ledger,transport);bridge=NativeBridge(gateway)
    from cognitive_architecture_lab_v1.src.public_runner.render import render_public_prompt
    prompt=render_public_prompt(task);engine=None;result=None;error=None
    try:
        with bridge.run_scope():
            if condition=='DIRECT':result=run_direct({'prompt':prompt},bridge)
            elif condition=='SELF_REFLECT':result=run_self_reflect({'prompt':prompt},bridge)
            else:
                config=EngineConfig(ledger_dir=str(directory/'engine_trajectories'),candidate_generation='native',quality_evaluation=True,llm_classification=False,max_run_calls=36)
                engine=EndEngine(config,provider=bridge,judge_provider=ModelJudgeProvider(bridge))
                r=engine.run(prompt,mode=None,max_cycles=3)
                result={'answer':r.answer,'termination':r.termination_reason.value,'iterations':r.iterations,'best_candidate_id':r.best_candidate_id,'latest_candidate_id':r.latest_candidate_id}
    except Exception as e:error=type(e).__name__
    finally:closed=gateway.close_generation(run_id)
    trajectory=engine.last_trajectory if engine is not None else None
    if condition=='FROZEN_CURRENT_END':
        candidates=(trajectory or {}).get('candidates',[]);c0=candidates[0].get('answer_content',candidates[0].get('content')) if candidates else None
        final=(result or {}).get('answer');termination=(result or {}).get('termination','EXTERNAL_BLOCKER')
    else:
        stages=(result or {}).get('stages',{});c0=stages.get('initial',stages.get('answer'));final=(result or {}).get('answer');termination='EXTERNAL_BLOCKER' if error else 'COMPLETED'
    if c0 is None:
        first=next((a for a in ledger.state()['attempts'] if a.get('candidate') and a['run_id']==run_id),None)
        if first:c0=first['response_text']
    if error=='RunBudgetExceeded':termination='BUDGET_EXHAUSTED'
    report={'namespace':'MOCK_WIRING_ONLY_NOT_EMPIRICAL','run_id':run_id,'task_id':task['task_id'],'condition':condition,'complete_public_request':prompt,'C0':c0,'FINAL':final,'termination_reason':termination,'error':error,'iterations':(result or {}).get('iterations'),'physical_attempts':ledger.summary(run_id)['physical_attempts'],'accounting':ledger.summary(run_id),'historical_adapter_call_log':bridge.log.entries,'sealed_requests':gateway.seals,'provider_records':transport.calls,'generation_closed':closed,'engine_trajectory':trajectory,'model_identity':bridge.metadata(),'no_scoring_performed':True}
    (directory/'MOCK_REPLAY.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return report
