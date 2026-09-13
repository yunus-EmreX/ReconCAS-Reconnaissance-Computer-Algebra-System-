import unittest
import sys
import os

# Üst dizindeki core modüllerini içeri aktarabilmek için path eklenir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.math_engine import MathEngine, UnsafeExpressionException, MathError

class TestMathEngine(unittest.TestCase):

    def test_basic_evaluation(self):
        # Temel aritmetik ve faktöriyel testleri
        self.assertEqual(MathEngine.evaluate_basic("587 - 325"), 262)
        self.assertEqual(MathEngine.evaluate_basic("sqrt(9)"), 3)
        self.assertEqual(MathEngine.evaluate_basic("12!"), 479001600)

    def test_exp_bug_fix(self):
        # exp() fonksiyonunun x->* manipülasyonundan zarar görmediğini test eder
        res = MathEngine.evaluate_basic("exp(0)")
        self.assertEqual(res, 1.0)

    def test_security_whitelist_injection(self):
        # Zararlı kod enjeksiyonlarının Whitelist tarafından kesin olarak engellenmesi
        malicious_inputs = [
            "__import__('os').system('dir')",
            "x; print('hacked')",
            "eval('1+1')",
            "foo(x)"
        ]
        for payload in malicious_inputs:
            with self.subTest(payload=payload):
                with self.assertRaises(UnsafeExpressionException):
                    MathEngine.evaluate_basic(payload)

    def test_advanced_analysis_roots(self):
        # Polinom kök bulma testi (x^2 + 3x - 4 = 0)
        is_eq, expr, roots = MathEngine.analyze_advanced("x^2 + 3x - 4 = 0")
        self.assertTrue(is_eq)
        self.assertIn(-4, roots)
        self.assertIn(1, roots)

if __name__ == '__main__':
    unittest.main()
