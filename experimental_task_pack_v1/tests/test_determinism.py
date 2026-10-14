import copy
import json
import locale
import random
import unittest
from unittest.mock import patch
from experimental_task_pack_v1.evaluators import evaluate_answer
from experimental_task_pack_v1.tests.test_evaluators import fixtures,good

class DeterminismTests(unittest.TestCase):
    def test_repetition_order_and_no_shared_state(self):
        fs=fixtures();baseline={f['fixture_id']:evaluate_answer(f['task_id'],f['candidate_content']) for f in fs}
        order=fs[:];random.Random(614).shuffle(order)
        for _ in range(3):
            for f in order:self.assertEqual(evaluate_answer(f['task_id'],f['candidate_content']),baseline[f['fixture_id']])
        altered=copy.deepcopy(baseline[fs[0]['fixture_id']]);altered['dimensions'].clear()
        self.assertEqual(evaluate_answer(fs[0]['task_id'],fs[0]['candidate_content']),baseline[fs[0]['fixture_id']])
    def test_key_order_crlf_escaping_and_locale_independence(self):
        for tid in ('EXP-001','EXP-002'):
            text=good(tid);obj=json.loads(text);expected=evaluate_answer(tid,text)
            other=json.dumps(dict(reversed(list(obj.items()))),ensure_ascii=True,indent=2).replace('\n','\r\n')
            self.assertEqual(evaluate_answer(tid,other),expected)
            with patch.object(locale,'localeconv',side_effect=AssertionError('No locale dependency')):
                self.assertEqual(evaluate_answer(tid,other),expected)
            escaped=text.replace('"scope"','"sc\\u006fpe"')
            self.assertEqual(evaluate_answer(tid,escaped),expected)
    def test_no_runtime_or_network_authority_dependencies(self):
        import socket,subprocess,urllib.request,time
        with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')), \
            patch.object(socket,'getaddrinfo',side_effect=AssertionError('No network')), \
            patch.object(subprocess,'run',side_effect=AssertionError('No child execution')), \
            patch.object(urllib.request,'urlopen',side_effect=AssertionError('No network')), \
            patch.object(time,'time',side_effect=AssertionError('No time-dependent scoring')):
            for tid in ('EXP-001','EXP-002'):self.assertTrue(evaluate_answer(tid,good(tid))['overall_pass'])
    def test_deterministic_error_classification(self):
        for text in ('','{','{"x":NaN}','{"scope":1,"scope":2}','<think>x</think>{}'):
            first=evaluate_answer('EXP-001',text)
            for _ in range(4):self.assertEqual(evaluate_answer('EXP-001',text),first)
    def test_no_internal_score_input_or_extra_call_reward(self):
        import inspect
        signature=inspect.signature(evaluate_answer)
        for field in ('quality_gate','confidence','operator_utility','model_agreement','information_gain','jev_decision','calls'):
            self.assertNotIn(field,signature.parameters)

if __name__=='__main__':unittest.main()
