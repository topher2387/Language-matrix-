"""Behavioral acceptance of the trusted, cooperative local execution boundary."""
import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from language_matrix import capabilities as cap

ROOT = Path(__file__).resolve().parents[1]

class ExecutionLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)
        self.elapsed = 0.0
        self.calls = []
        self.request = json.loads((ROOT/'docs/contracts/sample-capability-request.json').read_text())
        self.request.update(capability='lesson.generate', output_schema='lesson.v1', provider='local',
                            permissions=['local.generate'], deadline_utc='2030-01-01T00:05:00Z')
        self.request['policy'].update(max_attempts=2, timeout_seconds=3)
        self.lesson = json.loads((ROOT/'docs/contracts/sample-lesson.json').read_text())

    def handler(self, request, context):
        self.calls.append(copy.deepcopy(request))
        context.checkpoint()
        return copy.deepcopy(self.lesson)

    def run_request(self, handler=None, grants=('local.generate',), cancelled=lambda: False, handlers=None):
        if handlers is None:
            handlers = {('local', 'lesson.generate'): cap.HandlerSpec(
                handler or self.handler, required_permissions=('local.generate',))}
        return cap.execute_capability_request(self.request, handlers=handlers,
            granted_permissions=grants, utc_now=lambda:self.now,
            monotonic=lambda:self.elapsed, cancelled=cancelled)

    def test_no_grants_prevents_handler_invocation(self):
        result = self.run_request(grants=())
        self.assertEqual(result['status'], 'failure')
        self.assertEqual(self.calls, [])
        self.assertNotIn('output', result)

    def test_handler_required_permission_must_be_requested_and_granted(self):
        self.request['permissions'] = ['cache.read']
        result = self.run_request(grants=('cache.read','local.generate'))
        self.assertEqual(result['status'], 'failure')
        self.assertEqual(self.calls, [])

    def test_unknown_provider_or_handler_is_denied_before_invocation(self):
        for provider, handlers in [('unknown',None), ('local',{})]:
            with self.subTest(provider=provider,handlers=handlers):
                self.request['provider'] = provider
                self.assertEqual(self.run_request(handlers=handlers)['status'], 'failure')
                self.assertEqual(self.calls, [])

    def test_ready_requires_validated_output_and_records_pending(self):
        result = self.run_request()
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['states'], ['pending','ready'])
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['output'], self.lesson)
        self.assertEqual(len(self.calls), 1)

    def test_invalid_handler_output_never_becomes_ready(self):
        result = self.run_request(handler=lambda request,context: {'generated_code':'bad'})
        self.assertEqual(result['status'], 'failure')
        self.assertNotIn('output', result)

    def test_pre_cancelled_or_expired_never_invokes_handler(self):
        self.assertEqual(self.run_request(cancelled=lambda:True)['status'], 'failure')
        self.now += timedelta(hours=1)
        self.assertEqual(self.run_request()['status'], 'failure')
        self.assertEqual(self.calls, [])

    def test_cooperative_cancellation_during_handler_discards_output(self):
        cancelled = [False]
        def handler(request, context):
            cancelled[0] = True
            context.checkpoint()
            self.fail('checkpoint must stop cancelled handler')
        result = self.run_request(handler=handler,cancelled=lambda:cancelled[0])
        self.assertEqual(result['status'], 'failure')
        self.assertEqual(result['attempts'], 1)
        self.assertNotIn('output', result)

    def test_late_output_is_discarded_after_timeout_or_deadline(self):
        for limit in ('timeout','deadline'):
            with self.subTest(limit=limit):
                self.now = datetime(2030,1,1,tzinfo=timezone.utc)
                self.elapsed = 0
                def handler(request,context):
                    if limit=='timeout': self.elapsed=4
                    else:self.now+=timedelta(hours=1)
                    return self.lesson
                result=self.run_request(handler=handler)
                self.assertEqual(result['status'],'failure')
                self.assertNotIn('output',result)

    def test_transient_failure_retries_only_within_attempt_budget(self):
        calls=[]
        def flaky(request,context):
            calls.append(1)
            if len(calls)==1:raise RuntimeError('transient')
            return self.lesson
        result=self.run_request(handler=flaky)
        self.assertEqual(result['status'],'ready')
        self.assertEqual(result['attempts'],2)
        self.assertEqual(len(calls),2)
        calls.clear()
        def failing(request,context):
            calls.append(1)
            raise RuntimeError('permanent')
        result=self.run_request(handler=failing)
        self.assertEqual(result['status'],'failure')
        self.assertEqual(len(calls),2)

    def test_mutation_by_handler_cannot_extend_budget_or_change_output_contract(self):
        calls=[]
        original=copy.deepcopy(self.request)
        def handler(request,context):
            calls.append(1)
            request['policy']['max_attempts']=3
            request['output_schema']='audio-asset.v1'
            raise RuntimeError('retry')
        result=self.run_request(handler=handler)
        self.assertEqual(result['status'],'failure')
        self.assertEqual(len(calls),2)
        self.assertEqual(self.request,original)

    def test_malformed_requests_fail_without_invocation(self):
        for bad in (None, [], {'deadline_utc':17}):
            self.request=bad
            self.assertEqual(self.run_request()['status'],'failure')
        self.assertEqual(self.calls,[])

    def test_nonfinite_or_backward_clocks_fail_before_handler(self):
        for bad in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(clock=bad):
                self.elapsed=bad
                self.assertEqual(self.run_request()['status'],'failure')
                self.assertEqual(self.calls,[])
        ticks=iter([10.0,9.0])
        handlers={('local','lesson.generate'):cap.HandlerSpec(self.handler,required_permissions=('local.generate',))}
        result=cap.execute_capability_request(self.request,handlers=handlers,
            granted_permissions=('local.generate',),utc_now=lambda:self.now,
            monotonic=lambda:next(ticks))
        self.assertEqual(result['status'],'failure')
        self.assertEqual(self.calls,[])

    def test_validation_time_counts_toward_result_deadline(self):
        from unittest.mock import patch
        real_validate=cap.validate_output_schema
        def costly_validation(output,schema):
            errors=real_validate(output,schema)
            self.elapsed=4
            return errors
        with patch.object(cap,'validate_output_schema',side_effect=costly_validation):
            result=self.run_request()
        self.assertEqual(result['status'],'failure')
        self.assertNotIn('output',result)
