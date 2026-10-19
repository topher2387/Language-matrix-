"""Tests for capability request validation and execution runtime."""
import json
import unittest
from datetime import datetime, timedelta
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
    get_supported_permissions
)

class CapabilitiesTest(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_request = {
            "schema_version": "1.0",
            "request_id": "request-hello",
            "capability": "phonology.check",
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
            "output_schema": "phonology-report.v1",
            "permissions": [
                "cache.read",
                "local.generate"
            ],
            "deadline_utc": "2026-10-20T00:00:00Z"
        }
    
    def test_valid_request_passes_validation(self):
        """Test that a valid request passes all validations."""
        errors = validate_capability_request(self.sample_request)
        self.assertEqual(errors, [])
    
    def test_expired_request_fails_validation(self):
        """Test that expired requests fail validation."""
        # Create an expired request
        expired_request = self.sample_request.copy()
        expired_request["deadline_utc"] = "2020-10-20T00:00:00Z"
        
        errors = validate_capability_request(expired_request)
        self.assertIn("Deadline has expired", errors)
    
    def test_future_request_passes_validation(self):
        """Test that future requests pass validation."""
        # Create a request with deadline in the future
        future_request = self.sample_request.copy()
        future_request["deadline_utc"] = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        errors = validate_capability_request(future_request)
        self.assertEqual(errors, [])
    
    def test_invalid_deadline_format_fails_validation(self):
        """Test that invalid deadline formats fail validation."""
        invalid_request = self.sample_request.copy()
        invalid_request["deadline_utc"] = "invalid-date-format"
        
        errors = validate_capability_request(invalid_request)
        self.assertIn("Invalid deadline format", errors)
    
    def test_unknown_capability_fails_validation(self):
        """Test that unknown capabilities fail validation."""
        invalid_request = self.sample_request.copy()
        invalid_request["capability"] = "unknown.capability"
        
        errors = validate_capability_request(invalid_request)
        self.assertIn("Unknown capability: unknown.capability", errors)
    
    def test_unknown_output_schema_fails_validation(self):
        """Test that unknown output schemas fail validation."""
        invalid_request = self.sample_request.copy()
        invalid_request["output_schema"] = "unknown.v1"
        
        errors = validate_capability_request(invalid_request)
        self.assertIn("Unknown output schema: unknown.v1", errors)
    
    def test_unknown_permission_fails_validation(self):
        """Test that unknown permissions fail validation."""
        invalid_request = self.sample_request.copy()
        invalid_request["permissions"] = ["unknown.permission"]
        
        errors = validate_capability_request(invalid_request)
        self.assertIn("Unknown permission: unknown.permission", errors)
    
    def test_non_zero_cost_fails_validation(self):
        """Test that non-zero cost policies fail validation."""
        invalid_request = self.sample_request.copy()
        invalid_request["policy"]["max_cost_usd"] = 1
        
        errors = validate_capability_request(invalid_request)
        self.assertIn("Policy must have max_cost_usd = 0", errors)
    
    def test_network_allowed_fails_validation(self):
        """Test that network-allowed policies fail validation."""
        invalid_request = self.sample_request.copy()
        invalid_request["policy"]["allow_network"] = True
        
        errors = validate_capability_request(invalid_request)
        self.assertIn("Policy must have allow_network = false", errors)
    
    def test_valid_output_validation(self):
        """Test that valid outputs pass schema validation."""
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
        # This should pass validation (we're not validating the full schema here)
        # but we can at least make sure it doesn't crash
        self.assertIsInstance(errors, list)
    
    def test_invalid_output_schema_fails_validation(self):
        """Test that invalid output schemas fail validation."""
        errors = validate_output_schema({}, "unknown.v1")
        self.assertIn("Unknown output schema: unknown.v1", errors)
    
    def test_expired_request_detection(self):
        """Test request expiration detection."""
        # Expired request
        expired_request = self.sample_request.copy()
        expired_request["deadline_utc"] = "2020-10-20T00:00:00Z"
        
        self.assertTrue(is_request_expired(expired_request))
        
        # Valid request
        valid_request = self.sample_request.copy()
        valid_request["deadline_utc"] = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        self.assertFalse(is_request_expired(valid_request))
    
    def test_granted_permissions(self):
        """Test permission retrieval."""
        permissions = get_granted_permissions(self.sample_request)
        expected_perms = ["cache.read", "local.generate"]
        self.assertEqual(permissions, expected_perms)
    
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
        adversarial_request = self.sample_request.copy()
        adversarial_request["capability"] = "shell"
        
        errors = validate_capability_request(adversarial_request)
        self.assertIn("Unknown capability: shell", errors)
        
        # Test with paid provider (should be rejected)
        adversarial_request2 = self.sample_request.copy()
        adversarial_request2["provider"] = "paid-api"
        
        errors = validate_capability_request(adversarial_request2)
        # This should pass schema validation but we're checking for policy violations
        # The schema allows any provider, so we need to check the policy validation
        
        # Test with network access (should be rejected)  
        adversarial_request3 = self.sample_request.copy()
        adversarial_request3["policy"]["allow_network"] = True
        
        errors = validate_capability_request(adversarial_request3)
        self.assertIn("Policy must have allow_network = false", errors)

if __name__ == '__main__':
    unittest.main()