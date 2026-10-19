"""Boundary checks: unsafe/underspecified data must fail closed."""
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'contracts'

class ContractsTest(unittest.TestCase):
    def validate(self, name, data):
        path = ROOT / f'{name}-v1.schema.json'
        self.assertTrue(path.exists(), 'versioned schema must exist')
        schema = json.loads(path.read_text())
        Draft202012Validator.check_schema(schema)
        return list(Draft202012Validator(schema).iter_errors(data))

    def fixture(self, name):
        path = ROOT / f'sample-{name}.json'
        self.assertTrue(path.exists(), 'documented fixture must exist')
        return json.loads(path.read_text())

    def test_samples_validate(self):
        for name in ('lesson', 'capability-request'):
            with self.subTest(name=name):
                self.assertEqual([], self.validate(name, self.fixture(name)))

    def test_lesson_requires_all_four_teaching_surfaces(self):
        for field in ('english', 'hangul', 'spoken_phonetics', 'phonology'):
            lesson = self.fixture('lesson')
            del lesson['units'][0][field]
            self.assertTrue(self.validate('lesson', lesson))

    def test_unknown_widget_and_generated_code_rejected(self):
        for update in ({'type': 'html', 'ref_id': 'u1'}, {'type': 'teaching_unit', 'ref_id': 'u1', 'html': '<script>evil()</script>'}):
            lesson = self.fixture('lesson')
            lesson['widgets'] = [update]
            self.assertTrue(self.validate('lesson', lesson))

    def test_requests_reject_paid_network_and_execution_controls(self):
        for mutate in (lambda x: x.update(capability='shell'), lambda x: x.update(provider='paid-api'), lambda x: x['policy'].update(max_cost_usd=1), lambda x: x['policy'].update(allow_network=True), lambda x: x['input'].update(command='rm -rf /'), lambda x: x.update(endpoint='https://evil.invalid')):
            request = self.fixture('capability-request')
            mutate(request)
            self.assertTrue(self.validate('capability-request', request))

    def test_bounded_limits_and_unknown_nested_fields(self):
        for key, value in [('max_attempts', 0), ('max_attempts', 4), ('timeout_seconds', 301), ('unknown', True)]:
            request = self.fixture('capability-request')
            request['policy'][key] = value
            self.assertTrue(self.validate('capability-request', request))

    def test_reviewed_status_requires_named_reviewer(self):
        for status in ('reviewed', 'verified'):
            for reviewer in (None, '', '   '):
                lesson = self.fixture('lesson')
                lesson['verification'].update(status=status, reviewer=reviewer)
                self.assertTrue(self.validate('lesson', lesson))

    def test_no_implicit_verified_status(self):
        lesson = self.fixture('lesson')
        del lesson['verification']['status']
        self.assertTrue(self.validate('lesson', lesson))

if __name__ == '__main__':
    unittest.main()
