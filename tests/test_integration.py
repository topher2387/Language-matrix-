"""
Test for the integration example showing how the bounded capability runtime 
would be used in P01/P02 work.
"""

import unittest
from integration_example import example_worker_integration, example_batch_processing

class IntegrationTest(unittest.TestCase):
    
    def test_single_capability_execution(self):
        """Test that a single capability can be executed through the runtime."""
        result = example_worker_integration()
        
        # Verify the result has expected structure
        self.assertIn('output_schema', result)
        self.assertIn('request_id', result)
        self.assertIn('capability', result)
        self.assertIsNotNone(result.get('result'))
        
    def test_batch_processing(self):
        """Test that batch processing works correctly."""
        results = example_batch_processing()
        
        # Should have processed 2 requests
        self.assertEqual(len(results), 2)
        
        # Both should have valid output schemas
        for result in results:
            self.assertIn('output_schema', result)
            self.assertIsNotNone(result.get('result'))

if __name__ == '__main__':
    unittest.main()