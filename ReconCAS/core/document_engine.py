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

    def __init__(self):
        self.ocr = OCREngine()

    # ------------------------------------------------------------------
    # Genel Giriş Noktası
    # ------------------------------------------------------------------
    def analyze_file(self, path: str, progress_cb=None) -> list:
        """
        Dosya türünü otomatik algılar ve uygun analiz yöntemini çağırır.

        Args:
            path       : Dosya yolu (.png / .jpg / .jpeg / .pdf)
            progress_cb: progress_cb(current, total) — opsiyonel GUI callback

        Returns:
            [{"index": int, "source": str, "equation": str}, ...]
        """
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

            equations = self.ocr.extract_from_array(img_array, debug=False)
            results = []
            for i, eq in enumerate(equations or [], start=1):
                results.append({"index": i, "source": "Görüntü", "equation": eq})

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

            # Büyük PDF uyarısı
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
                # 200 DPI render — yeterli çözünürlük, makul hız
                mat = fitz.Matrix(200 / 72, 200 / 72)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, 3
                )

                try:
                    equations = self.ocr.extract_from_array(img_array, debug=False)
                except OCRError:
                    equations = []

                for eq in (equations or []):
                    results.append({
                        "index": global_index,
                        "source": f"Sayfa {page_num + 1}",
                        "equation": eq
                    })
                    global_index += 1

            doc.close()

            if progress_cb:
                progress_cb(total_pages, total_pages)

            if truncated:
                # Uyarıyı listenin başına ekle (index=0 gösterge amaçlı)
                results.insert(0, {
                    "index": 0,
                    "source": "UYARI",
                    "equation": f"PDF cok buyuk — yalnizca ilk {MAX_PDF_PAGES} sayfa tarandı."
                })

            return results
        except DocumentError:
            raise
        except Exception as e:
            raise DocumentError(f"PDF analiz hatası: {e}")
