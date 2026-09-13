import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vision.ocr_engine import OCREngine

class TestOCREngine(unittest.TestCase):

    def test_text_to_equations_cleaning(self):
        raw_ocr_output = "587 — 325\n\nx^2 + lOx + I = 0"
        equations = OCREngine._parse_text_to_equations(raw_ocr_output)
        
        self.assertIn("587 - 325", equations)
        # l -> 1, I -> 1 dönüşümünün yapıldığını ancak fonksiyonların bozulmadığını doğrula
        self.assertTrue(any("10x" in eq or "1" in eq for eq in equations))

    def test_context_aware_function_protection(self):
        # 'log' ve 'cos' kelimelerindeki 'o' ve 'l' harflerinin sayıya dönüşmediğini test eder
        raw_input = "log(x) + cos(y)"
        equations = OCREngine._parse_text_to_equations(raw_input)
        
        self.assertIn("log(x) + cos(y)", equations)

    def test_is_actual_math_filter(self):
        # Matematiksel olmayan düz yazıları filtreleme testi
        self.assertFalse(OCREngine.is_actual_math("Hello World"))
        self.assertFalse(OCREngine.is_actual_math("15")) # Sadece sayı olanlar elenir
        self.assertTrue(OCREngine.is_actual_math("x + 5 = 10"))
        self.assertTrue(OCREngine.is_actual_math("sin(x)"))

if __name__ == '__main__':
    unittest.main()
