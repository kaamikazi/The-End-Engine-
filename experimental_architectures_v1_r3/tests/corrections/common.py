import json,os,subprocess,sys,time,unittest
from dataclasses import replace,asdict
from pathlib import Path
from unittest.mock import patch
from tests.helpers import temporary,request,task,Script,complete,gate,Ledger,canonical
from src.shared.session import Session,execute
from src.shared.publication import Publication,ArtifactIntegrity,PublicationFailure,RunBusy,StaleOwner
from src.shared.journals import verify_journals
from src.shared.strict_json import sha,read,NumericFault
from src.shared.wiring import baseline
from src.shared.baseline_contract import ContractAdmissionError
OUT=Path(__file__).resolve().parents[2];ROOT=OUT.parent;EVIDENCE=[]
def evidence(test,group,**values):EVIDENCE.append({'test':test.id(),'group':group,**values})
def partial(d):
    q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':[complete()]}),d);s.generate('INITIAL');return q,s
def finish_good(d):
    q=request('SPARSE_DELIBERATION');r=execute(q,Script({'INITIAL':[complete()],'SPARSE_GATE':[gate()]}),d);return q,r
def journal(d):return next((Path(d)/'wire').glob('*.jsonl'))
def write_lines(p,rows):p.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8',newline='\n')
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def wait(p):
    until=time.monotonic()+25
    while not p.exists():
        if time.monotonic()>until:raise TimeoutError('Test barrier timeout')
        time.sleep(.01)
def worker(mode,d,name='one',termination='INTERRUPTED'):
    return subprocess.Popen([sys.executable,'-B',str(OUT/'tests/corrections/process_worker.py'),mode,str(d),name,termination],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def collect(p):
    stdout,stderr=p.communicate(timeout=40);return {'exit_code':p.returncode,'stdout':stdout,'stderr':stderr}
