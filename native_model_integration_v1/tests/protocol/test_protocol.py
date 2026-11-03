import json,unittest
from dataclasses import replace
from tests.helpers import *
from v0351_core_regression_pilot.bench.providers import render
class ProtocolTests(unittest.TestCase):
    def test_actual_repository_rendering_preserved(self):
        q=ModelRequest('verification','public instruction',{'b':[2,1],'a':'data'},{'type':'object','properties':{}})
        p=expected(q,True,123);self.assertEqual(p['prompt'],render(q));self.assertEqual(p['format'],q.schema);self.assertEqual(validate_wire(p,q,True,123),json.dumps(p).encode())
    def test_native_initial_prompt_is_verbatim(self):
        q=ModelRequest('initial_candidate','EXACT\nPUBLIC',{},None);self.assertEqual(expected(q,False,11)['prompt'],q.prompt)
    def test_exact_settings_mapping(self):
        q=ModelRequest('direct_answer','x',{},None);p=expected(q,False,99);self.assertEqual(p['options'],{'temperature':.7,'top_p':.8,'num_predict':4096,'num_ctx':8192,'seed':99});self.assertIs(p['think'],False);self.assertIs(p['stream'],False)
    def test_tools_attachments_system_context_defaults_reject(self):
        q=ModelRequest('direct_answer','x',{},None);p=expected(q,False,11)
        for key in ('tools','functions','images','system','context','keep_alive','raw','metadata','conversation_id'):
            with self.subTest(key=key),self.assertRaises(BoundaryError):validate_wire(p|{key:'private'},q,False,11)
    def test_wire_mismatch_and_model_substitution_reject(self):
        q=ModelRequest('direct_answer','x',{},None)
        for change in ({'model':'other'},{'prompt':'changed'},{'stream':True}):
            with self.subTest(change=change),self.assertRaises(BoundaryError):validate_wire(expected(q,False,11)|change,q,False,11)
    def test_decoder_valid_nonstreaming(self):self.assertEqual(decode(completion('text'),SETTINGS.model)['response'],'text')
    def test_empty_and_refusal_are_inert_text(self):
        for text in ('','I cannot comply.','__import__("os").system("bad")'):
            self.assertEqual(decode(completion(text),SETTINGS.model)['response'],text)
    def test_malformed_missing_extra_tool_fields(self):
        for raw in (b'{bad',b'null',b'{}',completion('x',tools=[]),completion('x',total_tokens=15),completion('x',metadata={'key':'private'})):
            with self.subTest(raw=raw[:20]),self.assertRaises(ReceiptError):decode(raw,SETTINGS.model)
    def test_provider_error_and_incomplete(self):
        for raw in (b'{"error":"synthetic error"}',completion('prefix',done=False),completion('x',done_reason='unknown')):
            with self.assertRaises(ReceiptError):decode(raw,SETTINGS.model)
    def test_negative_boolean_nonfinite_usage(self):
        for val in (-1,True,1.5,float('nan'),float('inf')):
            d=json.loads(completion());d['eval_count']=val
            with self.subTest(value=str(val)),self.assertRaises(ReceiptError):decode(json.dumps(d).encode(),SETTINGS.model)
    def test_missing_usage_remains_absent(self):
        d=json.loads(completion());d.pop('prompt_eval_count');d.pop('eval_count');r=decode(json.dumps(d).encode(),SETTINGS.model);self.assertNotIn('prompt_eval_count',r);self.assertNotIn('eval_count',r)
    def test_cached_token_units_unknown_not_added(self):
        r=decode(completion(prompt_eval_cached_count=3),SETTINGS.model);self.assertNotIn('prompt_eval_count',r);self.assertEqual(r['eval_count'],5)
    def test_metrics_consistency(self):
        for changes in ({'load_duration':2000000},{'prompt_eval_cached_count':99},{'total_duration':-1}):
            with self.assertRaises(ReceiptError):decode(completion(**changes),SETTINGS.model)
    def test_model_identity_drift_rejects(self):
        with self.assertRaises(ReceiptError):decode(completion(model='substitute'),SETTINGS.model)
    def test_context_and_thinking_host_only(self):
        r=decode(completion('answer',context=[1,2],thinking='private reasoning metadata'),SETTINGS.model);self.assertEqual(r['response'],'answer')
    def test_duplicate_json_response_fields(self):
        raw=completion()[:-1]+b',"response":"changed"}'
        with self.assertRaises(ReceiptError):decode(raw,SETTINGS.model)
    def test_provider_and_duration_units_not_guessed(self):
        r=decode(completion(total_duration=1000000),SETTINGS.model);self.assertEqual(r['total_duration'],1000000);self.assertEqual(SETTINGS.model,'qwen3:4b')

    def test_identity_lock_detects_provider_and_digest_drift(self):
        from src.provider_protocol.version import VersionLock
        v=VersionLock();observed={'provider_version':'SYNTHETIC_VERSION','model':'qwen3:4b','model_digest':'SYNTHETIC_DIGEST_NOT_OBSERVED'};v.observe(observed);self.assertEqual(v.observe(observed),observed)
        for changed in ({'provider_version':'OTHER'},{'model_digest':'OTHER'},{'model':'other'}):
            with self.assertRaises(BoundaryError):v.observe(observed|changed)
    def test_unknown_live_identity_never_guessed(self):
        from src.provider_protocol.version import VersionLock
        v=VersionLock();self.assertIsNone(v.observed)
        with self.assertRaises(BoundaryError):v.observe({'model':'qwen3:4b'})
        with self.assertRaises(BoundaryError):v.require_live()
