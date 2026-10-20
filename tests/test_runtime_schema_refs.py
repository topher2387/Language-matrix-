"""Tests for runtime schema reference validation and hardening."""
import json
import unittest

from language_matrix.capabilities import _check_schema_refs


class SchemaRefTest(unittest.TestCase):
    def test_local_fragment_refs_allowed(self):
        """Test that local fragment references (starting with #) are allowed."""
        # Create a schema with local fragment reference
        schema_with_local_ref = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "$ref": "#/definitions/address"
                }
            },
            "definitions": {
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"}
                    }
                }
            }
        }

        # This should not raise any exception for local fragment refs
        try:
            _check_schema_refs(schema_with_local_ref)
            # Success - no exception raised
        except Exception as e:
            self.fail(f"Local fragment references should be allowed, but got: {e}")

    def test_external_url_refs_rejected_before_resolution(self):
        """Test that external URL references are rejected before resolution."""
        # Create a schema with external URL reference
        schema_with_external_ref = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "$ref": "https://example.com/schema.json#/definitions/address"
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            _check_schema_refs(schema_with_external_ref)
        self.assertIn("External", str(context.exception))

    def test_external_file_refs_rejected_before_resolution(self):
        """Test that external file references are rejected before resolution."""
        # Create a schema with external file reference
        schema_with_external_ref = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "$ref": "./external.schema.json#/definitions/address"
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            _check_schema_refs(schema_with_external_ref)
        self.assertIn("External", str(context.exception))

    def test_non_string_refs_rejected_before_resolution(self):
        """Test that non-string references are rejected before resolution."""
        # Create a schema with non-string reference
        schema_with_invalid_ref = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "$ref": 123  # Invalid: not a string
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            _check_schema_refs(schema_with_invalid_ref)
        self.assertIn("non-string", str(context.exception))

    def test_nested_external_refs_rejected_before_resolution(self):
        """Test that nested external references are rejected before resolution."""
        # Create a schema with nested external reference
        schema_with_nested_ref = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "$ref": "#/properties/address_ref"
                },
                "address_ref": {
                    "$ref": "https://example.com/schema.json#/definitions/address"
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            _check_schema_refs(schema_with_nested_ref)
        self.assertIn("External", str(context.exception))

    def test_mixed_valid_invalid_refs_rejected_before_resolution(self):
        """Test that schemas with both valid and invalid refs are rejected."""
        # Create a schema with mixed references
        schema_with_mixed_refs = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "local_ref": {
                    "$ref": "#/definitions/local_schema"
                },
                "external_ref": {
                    "$ref": "https://example.com/schema.json#/definitions/address"
                }
            },
            "definitions": {
                "local_schema": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"}
                    }
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            _check_schema_refs(schema_with_mixed_refs)
        self.assertIn("External", str(context.exception))

    def test_relative_path_refs_rejected(self):
        """Test that relative path references are rejected."""
        # Create a schema with relative path reference
        schema_with_relative_ref = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "$ref": "../external.schema.json#/definitions/address"
                }
            }
        }

        with self.assertRaises(ValueError) as context:
            _check_schema_refs(schema_with_relative_ref)
        self.assertIn("External", str(context.exception))

    def test_empty_fragment_refs_allowed(self):
        """Test that empty fragment references are allowed."""
        # Create a schema with empty fragment reference
        schema_with_empty_ref = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "$ref": "#"
                }
            }
        }

        # This should not raise any exception for valid fragment refs
        try:
            _check_schema_refs(schema_with_empty_ref)
            # Success - no exception raised
        except Exception as e:
            self.fail(f"Empty fragment references should be allowed, but got: {e}")

    def test_valid_local_refs_work(self):
        """Test that various valid local fragment references work correctly."""
        # Test with multiple levels of nested refs
        schema_with_nested_refs = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "$ref": "#/definitions/address"
                },
                "contact": {
                    "$ref": "#/properties/address/properties/city"
                }
            },
            "definitions": {
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"}
                    }
                }
            }
        }

        # This should not raise any exception for valid fragment refs
        try:
            _check_schema_refs(schema_with_nested_refs)
            # Success - no exception raised
        except Exception as e:
            self.fail(f"Valid local fragment references should be allowed, but got: {e}")


if __name__ == '__main__':
    unittest.main()
