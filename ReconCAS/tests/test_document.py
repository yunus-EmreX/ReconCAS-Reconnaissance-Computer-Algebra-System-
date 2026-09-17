import unittest
import sys
import os
import tempfile
import numpy as np
import cv2
from PIL import Image, ImageDraw
import pymupdf as fitz
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.document_engine import DocumentEngine, DocumentError, MAX_PDF_PAGES
from vision.ocr_engine import OCRError

class TestDocumentEngine(unittest.TestCase):

    def setUp(self):
        self.engine = DocumentEngine()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_synthetic_image(self, filename: str, text: str = 'x + 5 = 10') -> str:
        import cv2
        path = os.path.join(self.temp_dir.name, filename)
        img = np.full((120, 450, 3), 255, dtype=np.uint8)
        cv2.putText(img, text, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.imwrite(path, img)
        return path

    def _create_synthetic_pdf(self, filename: str, page_count: int = 1, text: str = 'x + 5 = 10') -> str:
        path = os.path.join(self.temp_dir.name, filename)
        doc = fitz.open()
        for i in range(page_count):
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 100), text, fontsize=24)
        doc.save(path)
        doc.close()
        return path

    def test_png_analysis(self):
        path = self._create_synthetic_image('test_sample.png', 'y - 3 = 7')
        results = self.engine.analyze_file(path)
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]['source'], 'Görüntü')
        self.assertIn('equation', results[0])
        self.assertIn('confidence', results[0])
        self.assertIn('is_valid', results[0])

    def test_jpg_analysis(self):
        path = self._create_synthetic_image('test_sample.jpg', '2*x + 4 = 12')
        results = self.engine.analyze_file(path)
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]['source'], 'Görüntü')

    def test_pdf_analysis(self):
        path = self._create_synthetic_pdf('single_page.pdf', page_count=1, text='3*x = 15')
        results = self.engine.analyze_file(path)
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]['source'], 'Sayfa 1')

    def test_pdf_multiple_pages(self):
        path = self._create_synthetic_pdf('multi_page.pdf', page_count=3, text='x + y = 5')
        results = self.engine.analyze_file(path)
        self.assertIsInstance(results, list)
        sources = {r['source'] for r in results}
        self.assertTrue(any('Sayfa 1' in s for s in sources))

    def test_pdf_page_limit(self):
        # BUG-012 & BUG-013: 35 sayfalik PDF ile 30 sayfa sinirini test et
        path = self._create_synthetic_pdf('oversized.pdf', page_count=35, text='x = 1')
        results = self.engine.analyze_file(path)
        self.assertIsInstance(results, list)
        # index=0 uyari satiri olmali
        warning_item = results[0]
        self.assertEqual(warning_item['source'], 'UYARI')
        self.assertIn(f'İlk {MAX_PDF_PAGES} sayfa analiz edildi', warning_item['equation'])

    def test_unsupported_extension(self):
        fake_file = os.path.join(self.temp_dir.name, 'doc.docx')
        with open(fake_file, 'w') as f:
            f.write('test content')
        with self.assertRaises(DocumentError):
            self.engine.analyze_file(fake_file)

    def test_missing_file(self):
        missing_path = os.path.join(self.temp_dir.name, 'non_existent.pdf')
        with self.assertRaises(DocumentError):
            self.engine.analyze_file(missing_path)

    def test_progress_callback(self):
        path = self._create_synthetic_pdf('progress_test.pdf', page_count=2, text='z + 1 = 9')
        calls = []
        def my_callback(curr, total):
            calls.append((curr, total))

        self.engine.analyze_file(path, progress_cb=my_callback)
        self.assertTrue(len(calls) > 0)
        self.assertEqual(calls[-1][0], calls[-1][1])

    def test_empty_document(self):
        empty_img = os.path.join(self.temp_dir.name, 'empty.png')
        with open(empty_img, 'wb'):
            pass
        results = self.engine.analyze_file(empty_img)
        self.assertEqual(results, [])

    def test_ocr_failure(self):
        path = self._create_synthetic_image('failure_test.png')
        with patch.object(self.engine.ocr, 'extract_from_array', side_effect=OCRError('Simulated OCR failure')):
            with self.assertRaises(DocumentError):
                self.engine.analyze_file(path)

if __name__ == '__main__':
    unittest.main()
