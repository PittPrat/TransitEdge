'''
import unittest
from Shrey.policy_agent import score

class TestPolicyAgent(unittest.TestCase):
    def test_score(self):
        result = score(30, 10, 2, 1)  # should be: 30 + 10*0.14 - 0.4 - 0.1 = 30.9
        self.assertAlmostEqual(result, 30.9, places=2)

if __name__ == '__main__':
    unittest.main()
'''

from Shared.policy_agent import score, estimate_co2
co2 = estimate_co2(30, 1.5)
print("CO2:", co2)
print("Score:", score(30, co2, 2, 1))