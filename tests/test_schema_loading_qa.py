"""Independent controller tests: worker must not modify this file."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator
from language_matrix import capabilities as c

class SchemaLoadingQA(unittest.TestCase):
    def load(self, schema):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / 'qa.json').write_text(json.dumps(schema))
            with patch.object(c, 'SCHEMA_ROOT', path):
                return c._load_schema('qa.json')

    def test_actual_refs_refused(self):
        for keyword in ['$ref', '$dynamicRef']:
            for ref in ['https://example.invalid/a', 'file:///tmp/secret', 'relative.json', '../other', '', 42, None]:
                with self.subTest(keyword=keyword, ref=ref), self.assertRaises(ValueError):
                    self.load({'allOf': [{'properties': {'value': {keyword: ref}}}]})

    def test_local_fragment_validates_real_instances(self):
        schema = self.load({'$defs': {'item': {'type': 'integer'}}, 'properties': {'value': {'$ref': '#/$defs/item'}}})
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors({'value': 3})), [])
        self.assertTrue(list(validator.iter_errors({'value': 'wrong'})))

    def test_literal_and_property_names_preserved(self):
        for schema in [{'properties': {'$ref': {'type': 'string'}}}, {'const': {'$ref': 'https://example.invalid/data'}}, {'enum': [{'$ref': 'relative-data'}]}, {'examples': [{'$ref': 42}]}, {'$defs': {'$ref': {'type': 'string'}}}]:
            with self.subTest(schema=schema):
                self.assertEqual(self.load(schema), schema)

    def test_validator_entrypoint_rejects_before_construction(self):
        for keyword in ['$ref', '$dynamicRef']:
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / 'capability-request-v1.schema.json').write_text(json.dumps({keyword: 'https://example.invalid/schema'}))
                with patch.object(c, 'SCHEMA_ROOT', root), patch.object(c, 'CAPABILITY_REQUEST_SCHEMA', None), patch.object(c, 'Draft202012Validator') as validator:
                    with self.assertRaises(ValueError):
                        c._get_validator()
                    validator.assert_not_called()

    def test_shipped_corpus(self):
        paths = list(c.SCHEMA_ROOT.glob('*.schema.json'))
        self.assertTrue(paths)
        for path in paths:
            self.assertIsInstance(c._load_schema(path.name), dict)

    def test_single_schema_keywords_guarded(self):
        for keyword in ['propertyNames', 'unevaluatedProperties', 'unevaluatedItems', 'contains', 'if', 'then', 'else', 'items']:
            with self.subTest(keyword=keyword), self.assertRaises(ValueError):
                self.load({keyword: {'$ref': 'relative.json'}})
