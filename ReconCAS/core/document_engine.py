import os
import numpy as np
from PIL import Image

# ---- Opsiyonel bağımlılık: PyMuPDF (PDF desteği için) ----
try:
    import pymupdf as fitz   # PyMuPDF >= 1.24 yeni API
    PDF_SUPPORTED = True
except ImportError:
    try:
        import fitz           # PyMuPDF < 1.24 eski API (fallback)
        PDF_SUPPORTED = True
    except ImportError:
        PDF_SUPPORTED = False

from vision.ocr_engine import OCREngine, OCRError

class DocumentError(Exception):
    """Dosya analizi hataları için özel sınıf"""
    pass

MAX_PDF_PAGES = 30  # Büyük PDF koruması — kullanıcı uyarılır


class DocumentEngine:
    """
    PNG / JPG / PDF dosyalarından matematiksel ifade çıkarır.
    OCREngine'i dahili olarak kullanır; ekran yakalamaya gerek olmadan
    dosya bazlı analiz yapar.
    """

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.pdf')

    def __init__(self):
        self.ocr = OCREngine()

    # ------------------------------------------------------------------
    # Genel Giriş Noktası
    # ------------------------------------------------------------------
    def analyze_file(self, path: str, progress_cb=None) -> list:
        """
        Dosya türünü otomatik algılar ve uygun analiz yöntemini çağırır.

        Args:
            path       : Dosya yolu (.png / .jpg / .jpeg / .bmp / .tiff / .tif / .pdf)
            progress_cb: progress_cb(current, total) — opsiyonel GUI callback

        Returns:
            [{"index": int, "source": str, "equation": str, "raw_text": str, "confidence": float, "is_valid": bool}, ...]
        """
        if not path or not os.path.exists(path):
            raise DocumentError(f"Dosya bulunamadı: {path}")

        if os.path.getsize(path) == 0:
            return []

        ext = os.path.splitext(path)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'):
            return self._process_image(path, progress_cb)
        elif ext == '.pdf':
            if not PDF_SUPPORTED:
                raise DocumentError(
                    "PDF desteği için 'pymupdf' kütüphanesi gerekli.\n"
                    "Lütfen: pip install pymupdf"
                )
            return self._process_pdf(path, progress_cb)
        else:
            raise DocumentError(f"Desteklenmeyen dosya türü: {ext}")

    # ------------------------------------------------------------------
    # Görüntü Dosyası Analizi
    # ------------------------------------------------------------------
    def _process_image(self, path: str, progress_cb=None) -> list:
        try:
            pil_img = Image.open(path).convert("RGB")
            img_array = np.array(pil_img)
            if progress_cb:
                progress_cb(0, 1)

            # BUG-010 & BUG-011: return_details=True ile zengin çıktı al
            raw_items = self.ocr.extract_from_array(img_array, debug=False, return_details=True)
            results = []
            for i, item in enumerate(raw_items or [], start=1):
                results.append({
                    "index": i,
                    "source": "Görüntü",
                    "raw_text": item.get("raw_text", ""),
                    "normalized_text": item.get("normalized_text", ""),
                    "equation": item.get("equation", ""),
                    "confidence": item.get("confidence", 0.0),
                    "is_valid": item.get("is_valid", False)
                })

            if progress_cb:
                progress_cb(1, 1)
            return results
        except OCRError as e:
            raise DocumentError(f"Görüntü OCR Hatası: {e}")
        except Exception as e:
            raise DocumentError(f"Görüntü analiz hatası: {e}")

    # ------------------------------------------------------------------
    # PDF Dosyası Analizi
    # ------------------------------------------------------------------
    def _process_pdf(self, path: str, progress_cb=None) -> list:
        try:
            doc = fitz.open(path)
            total_pages = len(doc)
            if total_pages == 0:
                doc.close()
                return []

            # BUG-013: Büyük PDF uyarısı
            original_total = total_pages
            truncated = False
            if total_pages > MAX_PDF_PAGES:
                truncated = True
                total_pages = MAX_PDF_PAGES

            results = []
            global_index = 1

            for page_num in range(total_pages):
                if progress_cb:
                    progress_cb(page_num, total_pages)

                page = doc[page_num]
                # 200 DPI render — yüksek çözünürlük
                mat = fitz.Matrix(200 / 72, 200 / 72)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, 3
                )

                try:
                    raw_items = self.ocr.extract_from_array(img_array, debug=False, return_details=True)
                except OCRError:
                    raw_items = []

                for item in (raw_items or []):
                    results.append({
                        "index": global_index,
                        "source": f"Sayfa {page_num + 1}",
                        "raw_text": item.get("raw_text", ""),
                        "normalized_text": item.get("normalized_text", ""),
                        "equation": item.get("equation", ""),
                        "confidence": item.get("confidence", 0.0),
                        "is_valid": item.get("is_valid", False)
                    })
                    global_index += 1

            doc.close()

            if progress_cb:
                progress_cb(total_pages, total_pages)

            if truncated:
                # BUG-013: Kullanıcıya açık ve net uyarı
                results.insert(0, {
                    "index": 0,
                    "source": "UYARI",
                    "raw_text": "",
                    "normalized_text": "",
                    "equation": f"⚠ PDF {original_total} sayfa içeriyor. İlk {MAX_PDF_PAGES} sayfa analiz edildi.",
                    "confidence": 100.0,
                    "is_valid": False
                })

            return results
        except DocumentError:
            raise
        except Exception as e:
            raise DocumentError(f"PDF analiz hatası: {e}")
