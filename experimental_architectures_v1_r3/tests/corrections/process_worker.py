"""Supervised deterministic offline process workers; reviewer/test artifacts only."""
import json,os,socket,sys,time,urllib.request
from pathlib import Path
from unittest.mock import patch
OUT=Path(__file__).resolve().parents[2];sys.path[0:0]=[str(OUT),str(OUT.parent)]
from tests.corrections.common import request,Session,Script,complete,wait,sha
from src.shared.publication import exclusive_publish

def deny(*a,**kw):raise AssertionError('No network in process workers')
def main():
    mode,d,name,termination=sys.argv[1:];d=Path(d);s=Session(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()]}),d)
    if mode=='lock_crash':
        with s.store.lock():(d/(name+'.ready')).write_text('locked');os._exit(73)
    if mode in ('owner_crash','hold_owner'):
        s.generate('INITIAL');(d/(name+'.ready')).write_text('owned')
        if mode=='hold_owner':wait(d/'crash_now')
        os._exit(73)
    if mode=='after_link':
        s.generate('INITIAL')
        def die(pending,final):exclusive_publish(pending,final);os._exit(73)
        with patch('src.shared.publication.exclusive_publish',side_effect=die):s.finish('INTERRUPTED')
    if mode=='finalize':
        (d/(name+'.ready')).write_text('admitted');wait(d/'go');answer={}
        try:
            s.restore_without_dispatch();r=s.finish(termination);answer={'status':'VERIFIED_TERMINAL','result_sha256':sha((d/'RESULT.json').read_bytes()),'payload_sha256':r['artifact_payload_sha256'],'candidate_hashes':[c['answer_sha256'] for c in r['result']['all_generated_candidates']]}
        except Exception as e:answer={'status':'REJECTED','exception':type(e).__name__}
        (d/(name+'.result.json')).write_text(json.dumps(answer),encoding='utf-8');return
    raise AssertionError('Unknown worker mode')
if __name__=='__main__':
    with patch.object(socket.socket,'connect',deny),patch.object(socket,'getaddrinfo',deny),patch.object(urllib.request.OpenerDirector,'open',deny):main()
