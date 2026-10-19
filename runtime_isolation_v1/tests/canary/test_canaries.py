import base64,codecs,json,os,secrets,unittest,urllib.parse
from tests.helpers import *
PROBES=[]
def private_markers(root):
    categories=('evaluator_fixture','scoring_metadata','reference_answer','environment','unrelated_file','fake_provider_secret','previous_conversation','host_accounting')
    values={k:secrets.token_hex(24) for k in categories}
    for k,v in values.items():(Path(root)/(k+'.private.txt')).write_text(v,encoding='utf-8')
    PROBES.append({'categories':list(categories),'fresh_marker_sha256':{k:sha(v.encode()) for k,v in values.items()},'raw_markers_published':False})
    return values

def encoded(v):return (v,base64.b64encode(v.encode()).decode(),v.encode().hex(),''.join('\\u%04x'%ord(c) for c in v),codecs.encode(v,'rot_13'),urllib.parse.quote(v,safe=''))
def no_markers(testcase,markers,data):
    text=data.decode('utf-8') if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False)
    for v in markers.values():
        for representation in encoded(v):testcase.assertNotIn(representation,text)
class CanaryTests(unittest.TestCase):
    def test_all_private_sources_absent_from_exact_wire_and_provider_logs(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d,run_id=values['host_accounting'])
            old=os.environ.get('RUNTIME_PRIVATE_CANARY');os.environ['RUNTIME_PRIVATE_CANARY']=values['environment']
            try:
                with e.ledger.lock():
                    state=e.ledger._read();state['host_private_metadata']=values;e.ledger._write(state)
                e.send(spec(run_id=values['host_accounting']));no_markers(self,values,e.transport.sent[0]);no_markers(self,values,e.transport.provider_logs)
            finally:
                if old is None:os.environ.pop('RUNTIME_PRIVATE_CANARY',None)
                else:os.environ['RUNTIME_PRIVATE_CANARY']=old
    def test_encoded_private_messages_reject_structurally(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d)
            for v in values.values():
                for representation in encoded(v):
                    with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(messages=[{'role':'user','content':representation}]))
            self.assertEqual(e.transport.sent,[]);self.assertEqual(e.ledger.state()['attempts'],[])
    def test_encoded_private_prior_context_handles_reject(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d)
            for representation in encoded(values['reference_answer']):
                with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=[representation]))
            self.assertEqual(e.transport.sent,[])
    def test_entire_configuration_object_cannot_serialize(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d)
            for field in ('config','experiment','environment','host_metadata','provider_kwargs'):
                with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(**{field:values}))
            self.assertEqual(e.transport.sent,[])
    def test_private_source_and_answers_not_admitted_as_task(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d);bad=task();bad['task_statement']=values['evaluator_fixture']+values['reference_answer']
            with self.assertRaises(BoundaryError):e.gateway.register(request('different',t=bad))
    def test_foreign_condition_candidate_reject(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d,responses=[response_bytes(values['reference_answer'])]);e.gateway.register(request('other',condition='SELF_REFLECT'));a=e.send(spec(run_id='other'))
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=[a['output_id']]))
            self.assertEqual(len(e.transport.sent),1);no_markers(self,values,e.transport.sent[0]) # first request didn't contain canned output
    def test_unrelated_conversation_and_absolute_paths_reject(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d)
            for value in (str(Path(d)/'previous_conversation.private.txt'),'E:/private/evaluator.py','../../fixtures/answer.json'):
                with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=[value]))
            self.assertEqual(e.transport.sent,[])
    def test_private_observation_not_forwarded(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d);a=e.send()
            for kind in ('EVALUATOR_SCORE','HUMAN_REVIEW','CORRECTION','REFERENCE_ANSWER'):
                with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec('c2',purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=[a['output_id']],observation_ids=[kind+':'+a['output_id']]))
    def test_unexpected_response_metadata_quarantined(self):
        with temporary() as d:
            values=private_markers(d);r=json.loads(response_bytes('candidate'));r['metadata']=values;e=Env(d,responses=[canonical(r)])
            with self.assertRaises(BoundaryError):e.send()
            no_markers(self,values,e.transport.sent[0]);no_markers(self,values,e.transport.provider_logs)
            self.assertIsNone(e.ledger.state()['attempts'][0].get('candidate'));self.assertEqual(e.gateway.close_generation('run')['outputs'],[])
    def test_fresh_markers_are_not_literal_denylist(self):
        with temporary() as d:
            values=private_markers(d)
            for p in (LAB/'src').rglob('*.py'):no_markers(self,values,p.read_bytes())

    def test_provider_exception_metadata_never_forwarded(self):
        from src.trusted_transport.transport import TransportFailure
        with temporary() as d:
            values=private_markers(d);e=Env(d)
            def fail(body):
                error=RuntimeError(values['fake_provider_secret']);error.metadata=values;raise error
            e.transport.exchange=fail # Controlled trusted-host error injection, not a model callback.
            with self.assertRaises(TransportFailure) as caught:e.send()
            no_markers(self,values,str(caught.exception));no_markers(self,values,e.transport.provider_logs);no_markers(self,values,e.ledger.state())
    def test_forged_context_snapshot_cannot_reach_gateway(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d)
            state=e.ledger.state();state['attempts'].append({'attempt_id':999,'run_id':'run','state':'SUCCEEDED','response_text':values['reference_answer'],'response_sha256':sha(values['reference_answer'].encode()),'candidate':{'output_id':'FORGED','task_id':'SYN-A'}})
            fake=spec(purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=['FORGED'])
            e.compiler._compile(fake,state) # Trusted compiler can only be safe with actual ledger provenance.
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(fake)
            self.assertEqual(e.transport.sent,[])

    def test_secret_cannot_be_smuggled_as_model_identifier(self):
        with temporary() as d:
            values=private_markers(d);e=Env(d)
            for key in ('model_identity','model_digest'):
                with self.subTest(field=key),self.assertRaises(BoundaryError):e.gateway.register(request('other',**{key:values['fake_provider_secret']}))
    def test_settings_need_reviewed_configuration_not_encoded_secret(self):
        with temporary() as d:
            e=Env(d)
            for changes in ({'seed_if_supported':123456789},{'context_window':16384},{'generation_parameters':{'temperature':.9,'top_p':.8,'think':False}}):
                with self.subTest(changes=changes),self.assertRaises(BoundaryError):e.gateway.register(request('other',**changes))
