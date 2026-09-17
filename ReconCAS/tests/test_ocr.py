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

        # BUG-005 & BUG-PDF-005: False-positive doğal dil ve sarkan operatörler kesinlikle elenmeli
        self.assertFalse(OCREngine.is_actual_math("crore/ serine iar"))
        self.assertFalse(OCREngine.is_actual_math("hello/world"))
        self.assertFalse(OCREngine.is_actual_math("=8"))
        self.assertFalse(OCREngine.is_actual_math("ly-"))
        self.assertTrue(OCREngine.is_actual_math("x/2"))
        self.assertTrue(OCREngine.is_actual_math("sin(x)/2"))

    def test_bug_006_and_pdf_token_confusion_correction(self):
        # BUG-006 & BUG-PDF-001..006: Token bazlı confusion düzeltmesi
        corr1, val1 = OCREngine.correct_ocr_confusion("ly+5=2")
        self.assertEqual(corr1, "y+5=2")
        self.assertTrue(val1)

        corr2, val2 = OCREngine.correct_ocr_confusion("lx-4=3")
        self.assertEqual(corr2, "x-4=3")
        self.assertTrue(val2)

        corr3, val3 = OCREngine.correct_ocr_confusion("Ix-4=3")
        self.assertEqual(corr3, "x-4=3")
        self.assertTrue(val3)

        corr4, val4 = OCREngine.correct_ocr_confusion("ly-3=9")
        self.assertEqual(corr4, "y-3=9")
        self.assertTrue(val4)

    def test_bug_pdf_007_expression_segmentation(self):
        # BUG-PDF-007: Aynı satırda yan yana duran çoklu denklemler ayrıştırılmalı
        sub1 = OCREngine._segment_line_into_equations("x+0=1 ly-3=9")
        self.assertEqual(sub1, ["x+0=1", "ly-3=9"])

        sub2 = OCREngine._segment_line_into_equations("x= 11 ly= 12")
        self.assertEqual(sub2, ["x= 11", "ly= 12"])

        # Tek denklem bölünmemeli
        sub3 = OCREngine._segment_line_into_equations("x + 5 = 10")
        self.assertEqual(sub3, ["x + 5 = 10"])

    def test_vertical_arithmetic_merging(self):
        # Dikey 4 İşlem (Alt alta toplama / çıkarma / çarpma / bölme)
        # Soru numarası '2.' filtrelenmeli ve '27' ile '+3' birleştirilmeli
        eqs1 = OCREngine._parse_text_to_equations("2.\n27\n+3\n---\n[ ]")
        self.assertIn("27 + 3", eqs1)

        eqs2 = OCREngine._parse_text_to_equations("45\n- 18")
        self.assertIn("45 - 18", eqs2)

        eqs3 = OCREngine._parse_text_to_equations("12\nx 4")
        self.assertIn("12 * 4", eqs3)

        eqs4 = OCREngine._parse_text_to_equations("10\n20\n+ 30")
        self.assertIn("10 + 20 + 30", eqs4)

    def test_trailing_equal_and_questions(self):
        # Çalışma kağıdı soru kalıpları: '27 + 3 = ?', '15 - 4 =', '7,41 ='
        self.assertTrue(OCREngine.is_actual_math("27 + 3 = ?"))
        self.assertTrue(OCREngine.is_actual_math("27 + 3 ="))
        self.assertTrue(OCREngine.is_actual_math("45 - 18"))
        self.assertTrue(OCREngine.is_actual_math("12 * 4"))
        self.assertTrue(OCREngine.is_actual_math("7,41 ="))

if __name__ == '__main__':
    unittest.main()