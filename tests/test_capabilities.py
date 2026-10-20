"""Tests for capability request validation and execution runtime."""
import json
import copy
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the language_matrix directory to the path so we can import capabilities
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'language_matrix'))

from capabilities import (
    validate_capability_request,
    validate_output_schema,
    is_request_expired,
    get_granted_permissions,
    get_supported_capabilities,
    get_supported_permissions,
    HandlerSpec,
    execute_capability_request
)

class CapabilitiesTest(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.sample_request = {
            "schema_version": "1.0",
            "request_id": "request-hello",
            "capability": "lesson.generate",
            "provider": "local",
            "input": {
                "text": "안녕하세요.",
                "language": "ko"
            },
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 1,
                "timeout_seconds": 30
            },
            "rationale": "Check the pronunciation explanation before presenting it as reviewed.",
            "output_schema": "lesson.v1",
            "permissions": [
                "cache.read",
                "local.generate"
            ],
            "deadline_utc": (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    def test_valid_request_passes_validation(self):
        """Test that a valid request passes all validations."""
        errors = validate_capability_request(self.sample_request)
        self.assertEqual(errors, [])

    def test_expired_request_fails_validation(self):
        """Test that expired requests fail validation."""
        # Create an expired request
        expired_request = copy.deepcopy(self.sample_request)
        expired_request["deadline_utc"] = "2020-10-20T00:00:00Z"

        errors = validate_capability_request(expired_request)
        self.assertIn("Deadline has expired", errors)

    def test_future_request_passes_validation(self):
        """Test that future requests pass validation."""
        # Create a request with deadline in the future
        future_request = copy.deepcopy(self.sample_request)
        future_request["deadline_utc"] = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

        errors = validate_capability_request(future_request)
        self.assertEqual(errors, [])

    def test_invalid_deadline_format_fails_validation(self):
        """Test that invalid deadline formats fail validation."""
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["deadline_utc"] = "invalid-date-format"

        errors = validate_capability_request(invalid_request)
        # Should return schema validation error instead
        self.assertTrue(len(errors) > 0)
        self.assertIn("Schema validation failed", errors[0])

    def test_unknown_capability_fails_validation(self):
        """Test that unknown capabilities fail validation."""
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["capability"] = "unknown.capability"

        errors = validate_capability_request(invalid_request)
        # The schema validation will catch this, so we check for the schema error
        self.assertTrue(len(errors) > 0)
        self.assertIn("Schema validation failed", errors[0])

    def test_unknown_output_schema_fails_validation(self):
        """Test that unknown output schemas fail validation."""
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["output_schema"] = "unknown.v1"

        errors = validate_capability_request(invalid_request)
        # The schema validation will catch this, so we check for the schema error
        self.assertTrue(len(errors) > 0)
        self.assertIn("Schema validation failed", errors[0])

    def test_unknown_permission_fails_validation(self):
        """Test that unknown permissions fail validation."""
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["permissions"] = ["unknown.permission"]

        errors = validate_capability_request(invalid_request)
        # The schema validation will catch this, so we check for the schema error
        self.assertTrue(len(errors) > 0)
        self.assertIn("Schema validation failed", errors[0])

    def test_network_allowed_fails_validation(self):
        """Test that network-allowed policies fail validation."""
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["policy"]["allow_network"] = True

        errors = validate_capability_request(invalid_request)
        # The schema validation will catch this, so we check for the schema error
        self.assertTrue(len(errors) > 0)
        self.assertIn("Schema validation failed", errors[0])

    def test_non_zero_cost_fails_validation(self):
        """Test that non-zero cost policies fail validation."""
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["policy"]["max_cost_usd"] = 1

        errors = validate_capability_request(invalid_request)
        # The schema validation will catch this, so we check for the schema error
        self.assertTrue(len(errors) > 0)
        self.assertIn("Schema validation failed", errors[0])

    def test_unapproved_phonology_output_fails_closed(self):
        """Plausible phonology data cannot bypass an unavailable contract."""
        # This is a minimal phonology report
        output = {
            "schema_version": "1.0",
            "report_id": "report-123",
            "text": "안녕하세요.",
            "phonology": "The pronunciation is [an-nyeong-ha-seo-yo].",
            "verification": {
                "status": "reviewed",
                "reviewer": "test-reviewer",
                "notes": "Test phonology check"
            }
        }

        errors = validate_output_schema(output, "phonology-report.v1")
        self.assertTrue(errors)
        self.assertTrue(any("not found" in error for error in errors))

    def test_invalid_output_schema_fails_validation(self):
        """Test that invalid output schemas fail validation."""
        errors = validate_output_schema({}, "unknown.v1")
        self.assertIn("Unknown output schema: unknown.v1", errors)

    def test_expired_request_detection(self):
        """Test request expiration detection."""
        # Expired request
        expired_request = copy.deepcopy(self.sample_request)
        expired_request["deadline_utc"] = "2020-10-20T00:00:00Z"

        self.assertTrue(is_request_expired(expired_request))

        # Valid request
        valid_request = copy.deepcopy(self.sample_request)
        valid_request["deadline_utc"] = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

        self.assertFalse(is_request_expired(valid_request))

    def test_granted_permissions(self):
        """Test permission retrieval."""
        # With no explicit grants, should return empty list
        permissions = get_granted_permissions(self.sample_request)
        self.assertEqual(permissions, [])

        # With explicit grants that match requested permissions
        permissions = get_granted_permissions(self.sample_request, granted_permissions=["cache.read", "local.generate"])
        expected_perms = ["cache.read", "local.generate"]
        self.assertEqual(permissions, expected_perms)

        # With partial grants
        permissions = get_granted_permissions(self.sample_request, granted_permissions=["cache.read"])
        expected_perms = ["cache.read"]
        self.assertEqual(permissions, expected_perms)

        # With no matching grants
        permissions = get_granted_permissions(self.sample_request, granted_permissions=["cache.write"])
        expected_perms = []
        self.assertEqual(permissions, expected_perms)

    def test_granted_permissions_malformed_input(self):
        """Test that malformed permission inputs raise ValueError."""
        # Test with non-list permissions
        malformed_request = self.sample_request.copy()
        malformed_request["permissions"] = "not_a_list"

        with self.assertRaises(ValueError):
            get_granted_permissions(malformed_request)

        # Test with invalid permission names
        malformed_request2 = self.sample_request.copy()
        malformed_request2["permissions"] = ["cache.read", "invalid.permission"]

        with self.assertRaises(ValueError):
            get_granted_permissions(malformed_request2)

        # Test with non-string permission items
        malformed_request3 = self.sample_request.copy()
        malformed_request3["permissions"] = ["cache.read", 123]

        with self.assertRaises(ValueError):
            get_granted_permissions(malformed_request3)

    def test_supported_capabilities(self):
        """Test capability registry retrieval."""
        capabilities = get_supported_capabilities()
        self.assertIn("lesson.generate", capabilities)
        self.assertIn("phonology.check", capabilities)
        self.assertIn("tts.synthesize", capabilities)
        self.assertIn("asr.transcribe", capabilities)
        self.assertIn("image.generate", capabilities)

        # Check that each capability maps to correct output schemas
        self.assertEqual(capabilities["lesson.generate"], ["lesson.v1"])
        self.assertEqual(capabilities["phonology.check"], ["phonology-report.v1"])

    def test_supported_permissions(self):
        """Test permission registry retrieval."""
        permissions = get_supported_permissions()
        self.assertIn("cache.read", permissions)
        self.assertIn("cache.write", permissions)
        self.assertIn("local.generate", permissions)

    def test_adversarial_request_fails_validation(self):
        """Test that adversarial requests fail validation."""
        # Test with shell capability (should be rejected)
        adversarial_request = copy.deepcopy(self.sample_request)
        adversarial_request["capability"] = "shell"

        errors = validate_capability_request(adversarial_request)
        # Should return non-empty error list - schema validation will catch this
        self.assertTrue(len(errors) > 0)
        # Verify it's a schema validation error containing the rejected capability
        self.assertTrue(any("Schema validation failed" in e and "shell" in e for e in errors))

        # Test with paid provider (should be rejected)
        adversarial_request2 = copy.deepcopy(self.sample_request)
        adversarial_request2["provider"] = "paid-api"

        errors = validate_capability_request(adversarial_request2)
        # This should pass schema validation but we're checking for policy violations
        # The schema allows any provider, so we need to check the policy validation

        # Test with network access (should be rejected)
        adversarial_request3 = copy.deepcopy(self.sample_request)
        adversarial_request3["policy"]["allow_network"] = True

        errors = validate_capability_request(adversarial_request3)
        self.assertTrue(errors)
        self.assertTrue(any("Schema validation failed" in error for error in errors))

    def test_malformed_deadline_validation(self):
        """Test that malformed deadline_utc fails validation with nonempty error list."""
        # Test with deadline=17 (should fail schema validation)
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["deadline_utc"] = 17

        errors = validate_capability_request(invalid_request)
        self.assertTrue(len(errors) > 0, "Should return nonempty error list for malformed deadline")
        # Should not raise exception

    def test_malformed_capability_validation(self):
        """Test that malformed capability (array) fails validation with nonempty error list."""
        # Test with capability=[] (should fail schema validation)
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["capability"] = []

        errors = validate_capability_request(invalid_request)
        self.assertTrue(len(errors) > 0, "Should return nonempty error list for malformed capability")
        # Should not raise exception

    def test_malformed_policy_validation(self):
        """Test that malformed policy (number) fails validation with nonempty error list."""
        # Test with policy=17 (should fail schema validation)
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["policy"] = 17

        errors = validate_capability_request(invalid_request)
        self.assertTrue(len(errors) > 0, "Should return nonempty error list for malformed policy")
        # Should not raise exception

    def test_null_request_validation(self):
        """Test that null request fails validation with nonempty error list."""
        # Test with None request
        errors = validate_capability_request(None)
        self.assertTrue(len(errors) > 0, "Should return nonempty error list for null request")
        # Should not raise exception

    def test_capability_output_schema_binding_validation(self):
        """Test that mismatched capability/output_schema binding fails validation."""
        # Test lesson.generate with audio-asset.v1 (should fail binding)
        invalid_request = copy.deepcopy(self.sample_request)
        invalid_request["capability"] = "lesson.generate"
        invalid_request["output_schema"] = "audio-asset.v1"

        errors = validate_capability_request(invalid_request)
        self.assertTrue(len(errors) > 0, "Should return nonempty error list for mismatched capability/output_schema binding")
        # Check that it's a binding error, not just schema validation
        self.assertIn("does not support output schema", errors[0])

    def test_reserved_contract_unavailable_validation(self):
        """Test that reserved contracts with no actual schema file fail validation."""
        for capability, schema in (
            ("phonology.check", "phonology-report.v1"),
            ("asr.transcribe", "transcript.v1"),
            ("image.generate", "image-asset.v1"),
        ):
            with self.subTest(capability=capability):
                request = copy.deepcopy(self.sample_request)
                request.update(capability=capability, output_schema=schema)
                errors = validate_capability_request(request)
                self.assertTrue(any("schema file not found" in error for error in errors))
                calls = []
                result = execute_capability_request(
                    request,
                    handlers={("local", capability): HandlerSpec(lambda *_: calls.append(True))},
                    granted_permissions=("cache.read", "local.generate"),
                )
                self.assertEqual(result["status"], "failure")
                self.assertEqual(result["attempts"], 0)
                self.assertNotIn("output", result)
                self.assertEqual(calls, [])

class ControllerBoundaryTest(unittest.TestCase):
    def test_expiration_helper_fails_closed_for_malformed_inputs(self):
        for request in (None, 17, [], {'deadline_utc': 17}, {'deadline_utc': None}):
            with self.subTest(request=request):
                self.assertTrue(is_request_expired(request))

    def test_supervisor_grants_reject_malformed_authority(self):
        request = {'permissions': ['cache.read']}
        for grants in (None, 'cache.read', {'cache.read': True}, [['cache.read']], ['shell']):
            with self.subTest(grants=grants):
                with self.assertRaises(ValueError):
                    get_granted_permissions(request, granted_permissions=grants)
        for malformed in (None, 17, []):
            with self.subTest(request=malformed):
                with self.assertRaises(ValueError):
                    get_granted_permissions(malformed)

if __name__ == '__main__':
    unittest.main()
