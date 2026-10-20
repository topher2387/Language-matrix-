"""Validate unregistered proposal only; no capability or teaching approval."""
import copy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1] / 'docs/proposals'

class AudioProposalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / 'audio-asset-v1.proposed.schema.json').read_text())
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())
        cls.sample = json.loads((ROOT / 'audio-asset-v1.proposed.sample.json').read_text())

    def test_unverified_unknown_license_sample_valid(self):
        self.assertEqual(list(self.validator.iter_errors(self.sample)), [])
        self.assertEqual(self.sample['verification']['status'], 'unverified')
        self.assertEqual(self.sample['license_info']['status'], 'unknown')

    def test_missing_required_fields_refused(self):
        for key in self.schema['required']:
            value = copy.deepcopy(self.sample)
            del value[key]
            with self.subTest(key=key):
                self.assertFalse(self.validator.is_valid(value))

    def test_evidence_and_reviewer_constraints(self):
        for field, status, id_key in [('license_info', 'evidenced', 'evidence_id'), ('verification', 'reviewed', 'reviewer'), ('verification', 'verified', 'reviewer')]:
            value = copy.deepcopy(self.sample)
            value[field]['status'] = status
            self.assertFalse(self.validator.is_valid(value))
            value[field][id_key] = 'fixture-evidence'
            self.assertTrue(self.validator.is_valid(value))  # Shape only, never trusted authority.

    def test_metadata_negative_cases(self):
        for key, invalid in [('asset_id', '../audio'), ('voice_id', 'https://example.invalid'), ('content_hash', 'abc'), ('format', 'mp3'), ('sample_rate_hz', 7999), ('channels', 3), ('duration_seconds', 0), ('duration_seconds', 601)]:
            value = copy.deepcopy(self.sample)
            value[key] = invalid
            with self.subTest(key=key, invalid=invalid):
                self.assertFalse(self.validator.is_valid(value))
        value = copy.deepcopy(self.sample)
        value['provenance']['generated_at_utc'] = '2026-99-99T99:99:99Z'
        self.assertFalse(self.validator.is_valid(value))

    def test_unknown_fields_rejected_at_each_object_boundary(self):
        for key in [None, 'license_info', 'verification', 'provenance']:
            value = copy.deepcopy(self.sample)
            target = value if key is None else value[key]
            target['unexpected'] = 'x'
            with self.subTest(key=key):
                self.assertFalse(self.validator.is_valid(value))
