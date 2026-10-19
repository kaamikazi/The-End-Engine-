import tempfile
from pathlib import Path
from src.interfaces.contracts import RunRequest
LAB=Path(__file__).resolve().parents[1]
SCRATCH=LAB/'validation'/'scratch'
def temporary():
    SCRATCH.mkdir(parents=True,exist_ok=True)
    assert SCRATCH.resolve().is_relative_to(LAB.resolve())
    return tempfile.TemporaryDirectory(dir=SCRATCH)
def task():return {'task_id':'SYN-ONLY','title':'Synthetic echo','task_statement':'Return supplied public word. No external facts.','input':{'word':'blue'},'output_contract':{'word':'string'},'public_reference_ids':[]}
def request(condition='DIRECT',run_id='run',**kw):
    values=dict(task_id='SYN-ONLY',public_task_payload=task(),model_identity='dummy-no-model',model_digest='dummy-v1',generation_parameters={'temperature':.7,'top_p':.8,'think':False},seed_if_supported=11,context_window=8192,maximum_output_tokens=4096,condition_id=condition,attempt_budget=36,token_budget=30000,wall_time_budget=1800,run_id=run_id)
    values.update(kw);return RunRequest(**values)
