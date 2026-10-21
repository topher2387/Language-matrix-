import unittest
from ranges import merge_ranges
class RangesTests(unittest.TestCase):
    def test_empty(self): self.assertEqual(merge_ranges([]), [])
    def test_sorted_merged(self): self.assertEqual(merge_ranges([(5,7),(1,2),(3,4),(10,10)]),[(1,7),(10,10)])
    def test_no_mutation(self):
        a=[(5,8),(1,2)];merge_ranges(a);self.assertEqual(a,[(5,8),(1,2)])
    def test_negative_duplicate(self): self.assertEqual(merge_ranges([(-3,-1),(-1,2),(4,4),(4,4)]),[(-3,2),(4,4)])
    def test_reversed(self):
        with self.assertRaises(ValueError): merge_ranges([(3,1)])
if __name__=='__main__': unittest.main()
