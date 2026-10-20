"""Tests for the offline fixture validation CLI."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

class ValidateFixtureCLITest(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.script_path = Path(__file__).resolve().parents[1] / 'tools' / 'validate_fixture.py'
        self.sample_lesson_path = Path(__file__).resolve().parents[1] / 'docs' / 'contracts' / 'sample-lesson.json'
        self.sample_capability_path = Path(__file__).resolve().parents[1] / 'docs' / 'contracts' / 'sample-capability-request.json'
        
    def run_cli(self, schema_name, file_path, *, cwd=None):
        """Run the CLI with given arguments and return exit code."""
        result = subprocess.run([
            sys.executable, str(self.script_path), schema_name, str(file_path)
        ], capture_output=True, text=True,
           cwd=str(Path(__file__).resolve().parents[1]) if cwd is None else cwd)
        return result.returncode, result.stdout, result.stderr
    
    def test_valid_lesson(self):
        """Test that valid lesson fixture passes validation."""
        exit_code, stdout, stderr = self.run_cli('lesson', self.sample_lesson_path)
        self.assertEqual(exit_code, 0, f"Valid lesson should pass but failed with: {stderr}")
    
    def test_valid_capability_request(self):
        """Test that valid capability request fixture passes validation."""
        exit_code, stdout, stderr = self.run_cli('capability-request', self.sample_capability_path)
        self.assertEqual(exit_code, 0, f"Valid capability request should pass but failed with: {stderr}")
    
    def test_schema_invalid_lesson(self):
        """Test that schema-invalid lesson fixture fails validation."""
        # Create a modified lesson fixture that's invalid
        with open(self.sample_lesson_path, 'r') as f:
            lesson_data = json.load(f)
        
        # Remove a required field to make it invalid
        del lesson_data['title']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(lesson_data, f)
            temp_file = f.name
        
        try:
            exit_code, stdout, stderr = self.run_cli('lesson', temp_file)
            self.assertEqual(exit_code, 1, "Schema-invalid lesson should fail validation")
            self.assertIn("Error", stderr)  # Should have error message
        finally:
            os.unlink(temp_file)
    
    def test_schema_invalid_capability_request(self):
        """Test that schema-invalid capability request fixture fails validation."""
        # Create a modified capability request fixture that's invalid
        with open(self.sample_capability_path, 'r') as f:
            cap_data = json.load(f)
        
        # Remove a required field to make it invalid
        del cap_data['capability']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cap_data, f)
            temp_file = f.name
        
        try:
            exit_code, stdout, stderr = self.run_cli('capability-request', temp_file)
            self.assertEqual(exit_code, 1, "Schema-invalid capability request should fail validation")
            self.assertIn("Error", stderr)  # Should have error message
        finally:
            os.unlink(temp_file)
    
    def test_malformed_json(self):
        """Test that malformed JSON fails validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            temp_file = f.name
        
        try:
            exit_code, stdout, stderr = self.run_cli('lesson', temp_file)
            self.assertEqual(exit_code, 2, "Malformed JSON should fail with code 2")
            self.assertIn("Error", stderr)  # Should have error message
        finally:
            os.unlink(temp_file)
    
    def test_missing_file(self):
        """Test that missing file fails validation."""
        exit_code, stdout, stderr = self.run_cli('lesson', '/non/existent/file.json')
        self.assertEqual(exit_code, 2, "Missing file should fail with code 2")
        self.assertIn("Error", stderr)  # Should have error message
    
    def test_unknown_schema(self):
        """Test that unknown schema fails validation."""
        exit_code, stdout, stderr = self.run_cli('unknown-schema', self.sample_lesson_path)
        self.assertEqual(exit_code, 2, "Unknown schema should fail with code 2")
        self.assertIn("Error", stderr)  # Should have error message
    
    def test_wrong_number_of_arguments(self):
        """Test that wrong number of CLI arguments fails."""
        result = subprocess.run([
            sys.executable, str(self.script_path), 'lesson'
        ], capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]))
        self.assertEqual(result.returncode, 2, "Wrong number of arguments should fail with code 2")
        self.assertIn("Usage", result.stderr)  # Should show usage
    
    def test_invocation_from_different_directory(self):
        """Test that CLI works when invoked from a different working directory."""
        with tempfile.TemporaryDirectory() as directory:
            exit_code, stdout, stderr = self.run_cli(
                'lesson', self.sample_lesson_path, cwd=directory)
            self.assertEqual(exit_code, 0, f"CLI should work from different directory but failed with: {stderr}")

    def test_working_directory_cannot_replace_registry_schema(self):
        """An unrelated cwd cannot supply a permissive replacement schema."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schemas = root / 'docs' / 'contracts'
            schemas.mkdir(parents=True)
            (schemas / 'lesson-v1.schema.json').write_text('{}')
            fixture = root / 'invalid.json'
            fixture.write_text('{}')
            exit_code, stdout, stderr = self.run_cli('lesson', fixture, cwd=directory)
            self.assertEqual(exit_code, 1, stderr)
            self.assertNotIn('Traceback', stderr)

    def test_library_rejects_unknown_schema_before_file_access(self):
        from tools.validate_fixture import validate_fixture
        from unittest.mock import patch
        with patch('builtins.open', side_effect=AssertionError('must not access files')):
            for name in ('invalid-schema', '../lesson', '/tmp/lesson'):
                with self.subTest(name=name):
                    self.assertEqual(validate_fixture(name, '/unused'), 2)

    def test_library_rejects_all_non_fragment_refs_before_validation(self):
        from tools.validate_fixture import validate_fixture
        from unittest.mock import patch, mock_open
        for ref in ('http://example.invalid/a', 'https://example.invalid/a',
                    'file:///tmp/schema.json', 'other.json', '//example.invalid/a#x'):
            schema = {'type': 'object', 'properties': {'x': {'$ref': ref}}}
            with self.subTest(ref=ref), patch('builtins.open', mock_open(read_data='{}')), \
                    patch('tools.validate_fixture.json.load', return_value=schema), \
                    patch('tools.validate_fixture.Draft202012Validator') as validator:
                self.assertEqual(validate_fixture('lesson', '/unused'), 2)
                validator.assert_not_called()
                validator.check_schema.assert_not_called()

    def test_library_allows_internal_refs_and_still_validates(self):
        from tools.validate_fixture import validate_fixture
        from unittest.mock import patch, mock_open
        schema = {'$defs': {'word': {'type': 'string'}},
                  'type': 'object', 'properties': {'x': {'$ref': '#/$defs/word'}}}
        for data, expected in (({'x': 'valid'}, 0), ({'x': 7}, 1)):
            with self.subTest(data=data), patch('builtins.open', mock_open(read_data='{}')), \
                    patch('tools.validate_fixture.json.load', side_effect=[schema, data]):
                self.assertEqual(validate_fixture('lesson', '/unused'), expected)

if __name__ == '__main__':
    unittest.main()
