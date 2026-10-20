"""Independent behavioral QA regressions for trusted local execution boundaries."""
import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from language_matrix import capabilities as cap

ROOT = Path(__file__).resolve().parents[1]


class RuntimeWorkerBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)
        self.elapsed = 0.0
        self.calls = []
        self.request = json.loads(
            (ROOT / 'docs/contracts/sample-capability-request.json').read_text()
        )
        self.request.update(
            capability='lesson.generate',
            output_schema='lesson.v1',
            provider='local',
            permissions=['local.generate'],
            deadline_utc='2030-01-01T00:05:00Z',
        )
        self.request['policy'].update(max_attempts=2, timeout_seconds=3)
        self.lesson = json.loads(
            (ROOT / 'docs/contracts/sample-lesson.json').read_text()
        )

    def handler(self, request, context):
        self.calls.append(copy.deepcopy(request))
        context.checkpoint()
        return copy.deepcopy(self.lesson)

    def execute(
        self,
        *,
        handler=None,
        handlers=None,
        grants=('local.generate',),
        utc_now=None,
        monotonic=None,
        cancelled=None,
    ):
        if handlers is None:
            handlers = {
                ('local', 'lesson.generate'): cap.HandlerSpec(
                    self.handler if handler is None else handler,
                    required_permissions=('local.generate',),
                )
            }
        utc_now = (lambda: self.now) if utc_now is None else utc_now
        monotonic = (lambda: self.elapsed) if monotonic is None else monotonic
        cancelled = (lambda: False) if cancelled is None else cancelled
        return cap.execute_capability_request(
            self.request,
            handlers=handlers,
            granted_permissions=grants,
            utc_now=utc_now,
            monotonic=monotonic,
            cancelled=cancelled,
        )

    def test_malformed_handler_specs_and_registry_fail_before_invocation(self):
        malformed_specs = {
            'non_callable_handler': cap.HandlerSpec(handler=17),
            'string_permissions': cap.HandlerSpec(
                self.handler, required_permissions='local.generate'
            ),
            'unknown_permission': cap.HandlerSpec(
                self.handler, required_permissions=('shell',)
            ),
            'duplicate_permissions': cap.HandlerSpec(
                self.handler,
                required_permissions=('local.generate', 'local.generate'),
            ),
            'non_string_permission': cap.HandlerSpec(
                self.handler, required_permissions=('local.generate', 7)
            ),
        }
        for name, spec in malformed_specs.items():
            with self.subTest(spec=name):
                self.calls.clear()
                result = self.execute(
                    handlers={('local', 'lesson.generate'): spec},
                    grants=('local.generate', 'cache.read', 'cache.write'),
                )
                self.assertEqual(result['status'], 'failure')
                self.assertEqual(result['states'], ['failure'])
                self.assertEqual(result['attempts'], 0)
                self.assertTrue(result['errors'])
                self.assertEqual(self.calls, [])
                self.assertNotIn('output', result)

        self.calls.clear()
        result = self.execute(handlers=[])
        self.assertEqual(result['status'], 'failure')
        self.assertEqual(result['states'], ['failure'])
        self.assertEqual(result['attempts'], 0)
        self.assertEqual(self.calls, [])
        self.assertNotIn('output', result)

    def test_malformed_supervisor_grants_deny_before_invocation(self):
        malformed_grants = (
            None,
            'local.generate',
            ['local.generate', 'local.generate'],
            ['local.generate', 'shell'],
            [['local.generate']],
        )
        for grants in malformed_grants:
            with self.subTest(grants=grants):
                self.calls.clear()
                result = self.execute(grants=grants)
                self.assertEqual(result['status'], 'failure')
                self.assertEqual(result['states'], ['failure'])
                self.assertEqual(result['attempts'], 0)
                self.assertTrue(result['errors'])
                self.assertEqual(self.calls, [])
                self.assertNotIn('output', result)

    def test_cancellation_during_retry_gap_prevents_second_attempt(self):
        cancelled = [False]

        def handler(request, context):
            self.calls.append(1)
            cancelled[0] = True
            raise RuntimeError('transient')

        result = self.execute(handler=handler, cancelled=lambda: cancelled[0])

        self.assertEqual(result['status'], 'failure')
        self.assertEqual(result['states'], ['pending', 'failure'])
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(len(self.calls), 1)
        self.assertIn('Execution was cancelled', result['errors'])
        self.assertNotIn('output', result)

    def test_cancellation_after_valid_handler_output_discards_result(self):
        cancelled = [False]

        def handler(request, context):
            self.calls.append(1)
            cancelled[0] = True
            return copy.deepcopy(self.lesson)

        result = self.execute(handler=handler, cancelled=lambda: cancelled[0])

        self.assertEqual(result['status'], 'failure')
        self.assertEqual(result['states'], ['pending', 'failure'])
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(len(self.calls), 1)
        self.assertIn('Execution was cancelled', result['errors'])
        self.assertNotIn('output', result)

    def test_invalid_utc_clocks_fail_before_handler_invocation(self):
        def raising_clock():
            raise RuntimeError('clock unavailable')

        invalid_clocks = {
            'not_datetime': lambda: '2030-01-01T00:00:00Z',
            'naive_datetime': lambda: datetime(2030, 1, 1),
            'raises': raising_clock,
        }
        for name, clock in invalid_clocks.items():
            with self.subTest(clock=name):
                self.calls.clear()
                result = self.execute(utc_now=clock)
                self.assertEqual(result['status'], 'failure')
                self.assertEqual(result['states'], ['failure'])
                self.assertEqual(result['attempts'], 0)
                self.assertTrue(result['errors'])
                self.assertEqual(self.calls, [])
                self.assertNotIn('output', result)


if __name__ == '__main__':
    unittest.main()
