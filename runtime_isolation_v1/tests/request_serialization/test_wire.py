import dataclasses,json,unittest
from pathlib import Path
from tests.helpers import *
from src.sealed_requests.boundary import inspect_final_wire
class WireTests(unittest.TestCase):
    def test_actual_final_bytes_captured(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec());e.gateway.dispatch(s);self.assertEqual(e.transport.sent,[s.payload_bytes]);w=inspect_final_wire(e.transport.sent[0]);self.assertEqual(w['tools'],[]);self.assertEqual(w['messages'][0]['role'],'user')
    def test_actual_full_payload_matches_expected_allowlist(self):
        from cognitive_architecture_lab_v1.src.public_runner.render import render_public_prompt
        with temporary() as d:
            e=Env(d);e.send();expected={'wire_version':'tool-free-recording-json-v1','model':'OFFLINE_DUMMY','parameters':{'temperature':.7,'top_p':.8,'think':False,'seed':11,'context_window':8192,'maximum_output_tokens':4096},'messages':[{'role':'user','content':render_public_prompt(task())}],'tools':[],'tool_choice':'none','stream':False,'stateless':True}
            self.assertEqual(e.transport.sent[0],canonical(expected))
    def test_host_metadata_absent(self):
        with temporary() as d:
            e=Env(d,run_id='HOST_ONLY_RUN');s=e.gateway.reserve_request(spec(run_id='HOST_ONLY_RUN'));e.gateway.dispatch(s)
            for v in (b'HOST_ONLY_RUN',b'call_id',b'physical_call_reservation',b'wire_sha256',b'condition_id',b'provenance_bytes'):self.assertNotIn(v,e.transport.sent[0])
    def test_unknown_call_fields_reject_before_reservation(self):
        with temporary() as d:
            e=Env(d)
            for key in ('messages','system','developer','metadata','provider_request','file','config'):
                with self.subTest(key=key),self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(**{key:'private'}))
            self.assertEqual(e.ledger.state()['attempts'],[]);self.assertEqual(e.transport.sent,[])
    def test_preconstructed_provider_object_raw_bytes_reject(self):
        with temporary() as d:
            e=Env(d)
            for obj in ({'messages':[]},b'{}',object()):
                with self.subTest(t=type(obj).__name__),self.assertRaises(BoundaryError):e.gateway.dispatch(obj)
    def test_forged_sealed_body_reject(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec());bad=dataclasses.replace(s,payload_bytes=b'{"tools":["shell"]}')
            with self.assertRaises(BoundaryError):e.gateway.dispatch(bad)
            self.assertEqual(e.transport.sent,[])
    def test_forged_reservation_reject(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec());bad=dataclasses.replace(s,physical_call_reservation=999)
            with self.assertRaises(BoundaryError):e.gateway.dispatch(bad)
    def test_extra_final_wire_field_reject(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec());w=json.loads(s.payload_bytes);w['metadata']={'private':True}
            with self.assertRaises(BoundaryError):inspect_final_wire(canonical(w))
    def test_duplicate_final_wire_keys_reject(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec());raw=s.payload_bytes[:-1]+b',"tools":[]}'
            with self.assertRaises(BoundaryError):inspect_final_wire(raw)
    def test_partial_serialization_reject(self):
        with temporary() as d:
            e=Env(d);s=e.gateway.reserve_request(spec())
            for raw in (s.payload_bytes[:-7],b'null',b'[]',b'\xff'):
                with self.subTest(raw=raw[:8]),self.assertRaises(BoundaryError):inspect_final_wire(raw)
    def test_identical_initial_bytes_six_conditions(self):
        bodies=[]
        for c in CONDITIONS:
            with temporary() as d:e=Env(d,condition=c);e.send();bodies.append(e.transport.sent[0])
        self.assertEqual(len(set(bodies)),1)
    def test_current_run_outputs_allowed_bounded_and_quoted(self):
        with temporary() as d:
            e=Env(d,responses=[response_bytes('first'),response_bytes('second')]);a=e.send();e.send(spec('c2',purpose='critique',instruction_id='PUBLIC_REVIEW',prior_output_ids=[a['output_id']]))
            content=json.loads(json.loads(e.transport.sent[1])['messages'][0]['content']);self.assertEqual(content['quoted_current_run_outputs'][0]['text'],'first');self.assertNotIn('evaluation',content)
    def test_public_observation_computed_not_forwarded(self):
        with temporary() as d:
            e=Env(d,responses=[response_bytes('{"word":"blue"}')]);a=e.send();e.send(spec('c2',purpose='critique',instruction_id='PUBLIC_REVIEW',prior_output_ids=[a['output_id']],observation_ids=['JSON_PARSE:'+a['output_id']]))
            content=json.loads(json.loads(e.transport.sent[1])['messages'][0]['content']);self.assertEqual(content['public_local_observations'][0]['value'],'PARSEABLE_JSON')
    def test_run_task_payload_must_match_public_source_order(self):
        with temporary() as d:
            e=Env(d);t=task();t['input']['word']='unapproved'
            with self.assertRaises(BoundaryError):e.gateway.register(request('different',t=t))
    def test_public_source_hash_required(self):
        with self.assertRaises(BoundaryError):Compiler({'SYN-A':(public_bytes(),'0'*64)})
    def test_unapproved_process_instruction_reject(self):
        with temporary() as d:
            e=Env(d)
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec(instruction_id='CUSTOM_SECRET_PROMPT'))
    def test_run_mutation_reject(self):
        with temporary() as d:
            e=Env(d);e.request.generation_parameters['temperature']=.9
            with self.assertRaises(ValueError):e.gateway.reserve_request(spec())

    def test_initial_history_is_forbidden(self):
        with temporary() as d:
            e=Env(d);a=e.send()
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec('c2',prior_output_ids=[a['output_id']]))
    def test_bounded_prior_context_not_silently_truncated(self):
        with temporary() as d:
            e=Env(d,responses=[response_bytes('x'*16001)]);a=e.send()
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec('c2',purpose='revision',instruction_id='PUBLIC_REVISION',prior_output_ids=[a['output_id']]))
    def test_final_settings_and_shapes_strict(self):
        with temporary() as d:
            e=Env(d);base=json.loads(e.gateway.reserve_request(spec()).payload_bytes)
            for changes in ({'parameters':[]},{'messages':[None]},{'model':{'tools':['shell']}},{'parameters':base['parameters']|{'seed':True}},{'parameters':base['parameters']|{'maximum_output_tokens':99999}}):
                with self.subTest(changes=changes),self.assertRaises(BoundaryError):inspect_final_wire(canonical(base|changes))

    def test_independent_alternative_cannot_inherit_prior_outputs(self):
        with temporary() as d:
            e=Env(d);a=e.send()
            with self.assertRaises(BoundaryError):e.gateway.reserve_request(spec('c2',purpose='alternative',instruction_id='PUBLIC_ALTERNATIVE',prior_output_ids=[a['output_id']]))
    def test_model_visible_output_handles_do_not_reveal_global_attempt_ids(self):
        with temporary() as d:
            e=Env(d);a=e.send();self.assertEqual(len(a['output_id']),26);self.assertNotEqual(a['output_id'],'O_1');e.send(spec('c2',purpose='critique',instruction_id='PUBLIC_REVIEW',prior_output_ids=[a['output_id']]))
            self.assertNotIn(b'physical_call_reservation',e.transport.sent[1]);self.assertNotIn(b'attempt_id',e.transport.sent[1])
