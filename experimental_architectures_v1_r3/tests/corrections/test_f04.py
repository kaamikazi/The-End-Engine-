from .common import *
from src.shared.observations import parse,ProtocolFault
class NumericSafetyTests(unittest.TestCase):
    def reject_output(self,token,location):
        text='{"item_id":"T-1","amount":'+token+',"status":"draft"}' if location=='required' else '{"item_id":"T-1","amount":7,"status":"draft","extra":{"values":['+token+']}}'
        with temporary() as d:
            script=Script({'INITIAL':[text]});r=execute(request('SPARSE_DELIBERATION'),script,d);self.assertEqual(script.seen,['INITIAL']);self.assertEqual(r['result']['termination_reason'],'INVALID_RESPONSE');self.assertIsNone(r['result']['final_candidate']);self.assertEqual(r['C0'],text);self.assertEqual(r['result']['total_tokens'],15);self.assertEqual(r['result']['physical_attempts'],1);self.assertTrue((Path(d)/'RESULT.json').exists());self.assertTrue(r['generation_closed']);canonical(r);evidence(self,'F04',token=token,location=location,termination=r['result']['termination_reason'],attempts=1,raw_output_preserved=True)
    def test_valid_finite_float_semantics_match_python(self):
        for token in ('1e-3','-2.5e2','1.7976931348623157e308','1.7976931348623158e308','5e-324','1e-999999','-0.0'):
            value=parse(token);self.assertEqual(value,json.loads(token));self.assertTrue(__import__('math').isfinite(value))
    def test_large_integer_boundary(self):
        self.assertEqual(parse('9'*4300),int('9'*4300))
        with self.assertRaises(NumericFault):parse('9'*4301)
    def test_duplicate_keys_and_depth_size_limits_preserved(self):
        for value in ('{"a":1,"a":2}','['*49+'0'+']'*49,' '*1000001+'{}'):
            with self.assertRaises(ProtocolFault):parse(value)
    def test_provider_numeric_metadata_failure_is_diagnosed(self):
        from native_model_integration_v1.src.provider_protocol.canned import completion
        raw=completion(json.dumps(complete())).replace(b'"eval_count": 5',b'"eval_count": 1e400')
        with temporary() as d:
            r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[raw]}),d);self.assertEqual(r['result']['termination_reason'],'EXTERNAL_BLOCKER');self.assertIsNone(r['result']['total_tokens']);self.assertIsNone(r['C0']);self.assertTrue((Path(d)/'RESULT.json').exists())
    def test_nonfinite_control_never_becomes_repair_evidence(self):
        with temporary() as d:
            g=gate();text=json.dumps(g).replace('"uncertainty": []','"uncertainty": [1e400]');r=execute(request('SPARSE_DELIBERATION'),Script({'INITIAL':[complete()],'SPARSE_GATE':[text]}),d);self.assertEqual(r['result']['termination_reason'],'INVALID_RESPONSE');self.assertEqual(r['result']['physical_attempts'],2)
    def test_local_serialization_failure_gets_coherent_protocol_terminal(self):
        with temporary() as d:
            q,s=partial(d);s.notes.append(float('inf'));r=s.finish('INTERRUPTED');self.assertEqual(r['result']['termination_reason'],'PROTOCOL_FAILURE');self.assertTrue((Path(d)/'RESULT.json').exists());self.assertIn('TERMINAL_SERIALIZATION_REJECTED',json.dumps(r));canonical(r);evidence(self,'F04',serialization_failure='nonfinite local metadata',diagnosed=True)
    def test_serialization_failure_injection_is_diagnosed_and_retry_is_bounded(self):
        with temporary() as d:
            q,s=partial(d);original=s.store.publish;calls=[]
            def injected(data):
                calls.append(1)
                if len(calls)==1:raise ValueError('synthetic serializer fault')
                return original(data)
            with patch.object(s.store,'publish',side_effect=injected):r=s.finish('INTERRUPTED')
            self.assertEqual(len(calls),2);self.assertEqual(r['result']['termination_reason'],'PROTOCOL_FAILURE');self.assertEqual(r['result']['physical_attempts'],1)
    def test_recovery_of_numeric_rejected_output_keeps_raw_history(self):
        with temporary() as d:
            q=request('SPARSE_DELIBERATION');s=Session(q,Script({'INITIAL':['{"x":1e400}']}),d)
            with self.assertRaises(NumericFault):s.generate('INITIAL')
            s.detach();script=Script({});r=execute(q,script,d);self.assertEqual(script.seen,[]);self.assertEqual(len(r['result']['all_generated_candidates']),1);self.assertIsNone(r['FINAL']);self.assertTrue(r['generation_closed'])
for token in ('1e400','-1e400','1e999999','NaN','Infinity','-Infinity'):
    for location in ('required','optional_nested_array'):
        def test(self,t=token,where=location):self.reject_output(t,where)
        setattr(NumericSafetyTests,'test_reject_'+token.replace('-','negative_').replace('+','positive_')+'_'+location,test)
