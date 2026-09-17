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

    def test_bug_001_unicode_math_tokens(self):
        # BUG-001: Unicode matematik karakterlerinin kabul edilmesi ve normalizasyonu
        self.assertEqual(MathEngine.evaluate_basic("2×3"), 6)
        self.assertEqual(MathEngine.evaluate_basic("10÷2"), 5)
        self.assertEqual(MathEngine.evaluate_basic("√16"), 4)
        
        is_eq, expr, _ = MathEngine.analyze_advanced("π*x")
        self.assertIn("pi*x", str(expr))

        is_eq, expr, _ = MathEngine.analyze_advanced("∞")
        self.assertIn("oo", str(expr))

        is_valid, _, _, _ = MathEngine.validate_expression("∫x dx")
        self.assertTrue(is_valid)

    def test_bug_002_safe_words_case_insensitivity(self):
        # BUG-002: Whitelist case variations (Abs vs abs, Matrix vs matrix, etc.)
        for case in ["Abs(x)", "abs(x)", "ABS(x)"]:
            is_valid, _, _, _ = MathEngine.validate_expression(case)
            self.assertTrue(is_valid, f"Failed for case: {case}")

        for matrix_case in ["Matrix([[1, 2], [3, 4]])", "matrix([[1, 2], [3, 4]])"]:
            is_valid, _, _, _ = MathEngine.validate_expression(matrix_case)
            self.assertTrue(is_valid, f"Failed for case: {matrix_case}")

        is_valid, _, _, _ = MathEngine.validate_expression("Eq(x, 5)")
        self.assertTrue(is_valid)

    def test_bug_003_syntax_aware_root_and_integral(self):
        # BUG-003: Syntax-aware √ ve ∫ parantez ve argüman koruması
        _, expr1, _ = MathEngine.analyze_advanced("√x")
        self.assertEqual(str(expr1), "sqrt(x)")

        _, expr2, _ = MathEngine.analyze_advanced("√(x+1)")
        self.assertEqual(str(expr2), "sqrt(x + 1)")

        _, expr3, _ = MathEngine.analyze_advanced("√x+1")
        self.assertEqual(str(expr3), "sqrt(x) + 1")

        _, expr4, _ = MathEngine.analyze_advanced("∫x dx")
        self.assertEqual(str(expr4), "x**2/2")

        _, expr5, _ = MathEngine.analyze_advanced("∫x")
        self.assertEqual(str(expr5), "x**2/2")

    def test_bug_016_absolute_value_syntax(self):
        # BUG-016: |x| -> Abs(x)
        self.assertEqual(MathEngine.evaluate_basic("|-5|"), 5)
        self.assertEqual(MathEngine.evaluate_basic("|x| + 5".replace("x", "3")), 8)
        _, expr, _ = MathEngine.analyze_advanced("|x+1|")
        self.assertEqual(str(expr), "Abs(x + 1)")

    def test_bug_015_operation_dispatcher(self):
        # BUG-015: First-class symbolic operation dispatch
        res_diff = MathEngine.dispatch_operation("diff(x**2, x)")
        self.assertEqual(str(res_diff["result"]), "2*x")

        res_int = MathEngine.dispatch_operation("integrate(x, x)")
        self.assertEqual(str(res_int["result"]), "x**2/2")

        res_solve = MathEngine.dispatch_operation("2*x - 6 = 0")
        self.assertEqual(res_solve["result"], [3])

    def test_bug_007_validate_expression(self):
        # BUG-007: Validation returns accurate status and parsed object
        is_val, formatted, parsed, err = MathEngine.validate_expression("3*x + 4 = 10")
        self.assertTrue(is_val)
        self.assertIsNone(err)

        is_val_bad, _, _, err_bad = MathEngine.validate_expression("x + 02H")
        self.assertFalse(is_val_bad)
        self.assertIsNotNone(err_bad)

    def test_basic_arithmetic_question_formats(self):
        # 4 İşlem soru kalıpları ve trailing '=' desteği
        self.assertEqual(MathEngine.evaluate_basic("27 + 3 = ?"), 30)
        self.assertEqual(MathEngine.evaluate_basic("27 + 3 ="), 30)
        self.assertEqual(MathEngine.evaluate_basic("45 - 18 ="), 27)
        self.assertEqual(MathEngine.evaluate_basic("12 * 4 ="), 48)
        self.assertEqual(MathEngine.evaluate_basic("84 / 4 ="), 21)
        self.assertEqual(MathEngine.evaluate_basic("7,41 ="), 7.41)

        # is_advanced ayrımı: saf aritmetik işlemler temel sayılmalı (Lab yerine basic eval)
        self.assertFalse(MathEngine.is_advanced("27 + 3"))
        self.assertFalse(MathEngine.is_advanced("27 + 3 = ?"))
        self.assertFalse(MathEngine.is_advanced("45 - 18 ="))
        self.assertTrue(MathEngine.is_advanced("x + 5 = 10"))

if __name__ == '__main__':
    unittest.main()