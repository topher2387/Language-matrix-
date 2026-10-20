#!/usr/bin/env python3
"""Tests for export_runtime_lesson tool."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import unittest

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.export_runtime_lesson import export_lesson


class TestRuntimeExport(unittest.TestCase):
    """Test cases for export_runtime_lesson functionality."""

    def test_export_lesson_default_success(self):
        """Test default lesson export produces valid JSON with nasalisation-1."""
        result = export_lesson()
        self.assertIsInstance(result, dict)
        # Validate it's a proper lesson-v1
        self.assertIn("schema_version", result)
        self.assertEqual(result["schema_version"], "1.0")
        self.assertIn("lesson_id", result)
        self.assertEqual(result["lesson_id"], "nasalisation-1")

    def test_export_lesson_default_selector_validation(self):
        """Test that default selector fails if nasalisation-1 is not in fixtures."""
        # This test will fail initially to demonstrate the issue
        with patch('tools.export_runtime_lesson.lessons._fixtures') as mock_fixtures:
            # Return empty fixtures list to simulate missing default
            mock_fixtures.return_value = []

            with self.assertRaises(ValueError) as context:
                export_lesson()
            self.assertIn("not found in fixtures", str(context.exception))

    def test_export_lesson_with_valid_selector(self):
        """Test lesson export with valid selector returns correct lesson."""
        result = export_lesson("liaison-1")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["lesson_id"], "liaison-1")

    def test_export_lesson_malformed_lesson_raises_valueerror(self):
        """Test that export fails when generate_lesson returns malformed lesson."""
        with patch('tools.export_runtime_lesson.generate_lesson') as mock_gen:
            # Mock generate_lesson to return a malformed lesson
            mock_gen.return_value = {"invalid": "lesson_data"}

            with self.assertRaises(ValueError) as context:
                export_lesson("nasalisation-1")
            mock_gen.assert_called_once()

    def test_export_lesson_no_grants_failure(self):
        """Test that export fails when no grants are provided."""
        with patch('tools.export_runtime_lesson.generate_lesson') as mock_gen:
            # Mock to avoid actual generation
            mock_gen.return_value = {"lesson_id": "test-lesson", "schema_version": "1.0"}

            with self.assertRaises(ValueError) as context:
                export_lesson(granted_permissions=())
            # Should fail due to permission check, not validation
            self.assertIn("Requested permission not granted", str(context.exception))
            mock_gen.assert_not_called()

    def test_export_lesson_cancelled_failure(self):
        """Test that export fails when cancelled."""
        with patch('tools.export_runtime_lesson.generate_lesson') as mock_gen:
            # Mock to avoid actual generation
            mock_gen.return_value = {"lesson_id": "test-lesson", "schema_version": "1.0"}

            with self.assertRaises(ValueError) as context:
                export_lesson(cancelled=lambda: True)
            self.assertIn("Execution was cancelled", str(context.exception))
            mock_gen.assert_not_called()


class TestRuntimeExportCLI(unittest.TestCase):
    """Test cases for export_runtime_lesson CLI."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool_path = Path(__file__).resolve().parents[1] / "tools" / "export_runtime_lesson.py"
        self.assertTrue(self.tool_path.exists())

    def test_cli_default_success(self):
        """Test CLI default export produces valid JSON."""
        result = subprocess.run(
            [sys.executable, str(self.tool_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1]
        )

        self.assertEqual(result.returncode, 0)
        self.assertNotEqual(len(result.stdout.strip()), 0)

        # Parse the output to verify it's valid JSON
        exported_data = json.loads(result.stdout)
        self.assertIsInstance(exported_data, dict)
        self.assertIn("schema_version", exported_data)
        self.assertEqual(exported_data["schema_version"], "1.0")
        self.assertEqual(exported_data["lesson_id"], "nasalisation-1")

    def test_cli_with_lesson_id(self):
        """Test CLI with --lesson-id argument."""
        result = subprocess.run(
            [sys.executable, str(self.tool_path), "--lesson-id", "liaison-1"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1]
        )

        self.assertEqual(result.returncode, 0)
        self.assertNotEqual(len(result.stdout.strip()), 0)

        # Parse the output to verify it's valid JSON
        exported_data = json.loads(result.stdout)
        self.assertIsInstance(exported_data, dict)
        self.assertIn("lesson_id", exported_data)
        self.assertEqual(exported_data["lesson_id"], "liaison-1")

    def test_cli_no_grants(self):
        """Test CLI with --no-grants flag."""
        result = subprocess.run(
            [sys.executable, str(self.tool_path), "--no-grants"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1]
        )

        # Should fail due to missing permissions
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Requested permission not granted", result.stderr)

    def test_cli_cancelled(self):
        """Test CLI with --cancelled flag."""
        result = subprocess.run(
            [sys.executable, str(self.tool_path), "--cancelled"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1]
        )

        # Should fail due to cancellation
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Execution was cancelled", result.stderr)

    def test_cli_unknown_selector_returns_error(self):
        """Test CLI with unknown --lesson-id returns error."""
        result = subprocess.run(
            [sys.executable, str(self.tool_path), "--lesson-id", "unknown-selector"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1]
        )

        # Should return error for unknown lesson ID
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown lesson ID", result.stderr)

    def test_cli_cross_cwd_success(self):
        """Test CLI works from different working directories."""
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                result = subprocess.run(
                    [sys.executable, str(self.tool_path)],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir
                )

                self.assertEqual(result.returncode, 0)
                self.assertNotEqual(len(result.stdout.strip()), 0)
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
