"""Validation previews must not claim reserved capabilities executed."""
import unittest
from integration_example import example_worker_integration, example_batch_processing

class IntegrationTest(unittest.TestCase):
    def test_single_capability_is_explicitly_blocked(self):
        result = example_worker_integration()
        self.assertEqual(result['status'], 'blocked')
        self.assertFalse(result['executed'])
        self.assertTrue(any('schema file not found' in e for e in result['errors']))
        self.assertNotIn('result', result)

    def test_batch_preserves_refusal_for_each_reserved_contract(self):
        results = example_batch_processing()
        self.assertEqual(len(results), 2)
        self.assertEqual([r['capability'] for r in results], ['phonology.check', 'tts.synthesize'])
        for result in results:
            self.assertEqual(result['status'], 'blocked')
            self.assertFalse(result['executed'])
            self.assertTrue(result['errors'])
            self.assertNotIn('result', result)
