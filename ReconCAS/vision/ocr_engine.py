import pytesseract
from PIL import ImageGrab, Image
import cv2
import numpy as np
import hashlib
import re
import os
import time

# Tesseract'in kurulu oldugu dizin
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRError(Exception):
    pass

class OCREngine:
    # Proje kok dizini: vision/ klasorununun bir ustu
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(BASE_DIR, "logs")

    def __init__(self):
        self.last_frame_hash = None
        # Log klasorunu her zaman proje kok dizinine olustur (mutlak yol)
        try:
            os.makedirs(OCREngine.LOG_DIR, exist_ok=True)
        except Exception as e:
            print(f">_ [UYARI] Log klasoru olusturulamadi. Windows izni reddetti: {e}")

    # ------------------------------------------------------------------
    # Goruntuyu OCR icin hazirla (ekran yakalama - bbox)
    # ------------------------------------------------------------------
    def _preprocess_image(self, bbox):
        try:
            pil_img = ImageGrab.grab(bbox)
            img_array = np.array(pil_img)
            return self._apply_preprocessing(img_array)
        except Exception as e:
            raise OCRError(f"Goruntu isleme hatasi: {str(e)}")

    # ------------------------------------------------------------------
    # Goruntuyu OCR icin hazirla (dosyadan gelen numpy array)
    # ------------------------------------------------------------------
    def _preprocess_from_array(self, img_array: np.ndarray) -> np.ndarray:
        try:
            return self._apply_preprocessing(img_array)
        except Exception as e:
            raise OCRError(f"Array on-isleme hatasi: {str(e)}")

    # ------------------------------------------------------------------
    # Ortak on-isleme pipeline (hem bbox hem array icin)
    # ------------------------------------------------------------------
    @staticmethod
    def _apply_preprocessing(img_array: np.ndarray) -> np.ndarray:
        # RGB -> BGR donusumu
        if img_array.ndim == 3 and img_array.shape[2] == 3:
            img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img = img_array.copy()

        # 30px beyaz cerceve: kenar kesme hatalarini onler
        pad = 30
        img = cv2.copyMakeBorder(img, pad, pad, pad, pad,
                                  cv2.BORDER_CONSTANT, value=[255, 255, 255])

        # Gri tonlama
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Karanlik Mod Koruyucu: ortalama < 127 ise rengi ters cevir
        if np.mean(gray) < 127:
            gray = cv2.bitwise_not(gray)

        # Adaptif olcekleme: hedef yukseklik 96px (daha yuksek = daha iyi LSTM performansi)
        h, w = gray.shape
        target_h = 96
        if h < target_h:
            scale = target_h / h
            gray = cv2.resize(gray, None, fx=scale, fy=scale,
                               interpolation=cv2.INTER_CUBIC)
        elif h > 600:
            # Cok buyuk goruntuleri kuc kucult (PDF sayfasi gibi)
            scale = 400 / h
            gray = cv2.resize(gray, None, fx=scale, fy=scale,
                               interpolation=cv2.INTER_AREA)

        # OTSU ikili eslikleme: gurultuyu temizler, karakterleri keskinlestirir
        _, binary = cv2.threshold(gray, 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Hafif dilate: ince yazilari kalinlastirir (Tesseract icin faydali)
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)

        return binary

    # ------------------------------------------------------------------
    # Coklu PSM modunda OCR — en iyi sonucu sec
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_with_multiple_psm(img: np.ndarray) -> str:
        """
        PSM 6 (uniform block), 11 (sparse text), 4 (single column) dener.
        En fazla matematiksel karakter iceren sonuc alinir.
        'Veri bulunamadi' hatalarini dramatik sekilde azaltir.
        """
        psm_modes = ['--oem 3 --psm 6', '--oem 3 --psm 11', '--oem 3 --psm 4']
        best_text = ""
        best_score = -1

        for config in psm_modes:
            try:
                text = pytesseract.image_to_string(img, config=config)
                # Puan: matematiksel sembol yogunlugu
                score = len(re.findall(r'[\d+\-*/=^().]', text))
                if score > best_score:
                    best_score = score
                    best_text = text
            except Exception:
                continue

        return best_text

    # ------------------------------------------------------------------
    # Metin -> denklem listesi donusumu
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_text_to_equations(text: str) -> list:
        if not text or not text.strip():
            return []

        # Unicode matematik sembolleri normalize et
        # Em-dash, en-dash, tire varyantlari -> standart tire
        text = text.replace('—', '-').replace('–', '-').replace('−', '-')
        text = re.sub(r'[_~]', '-', text)
        text = text.replace('×', '*').replace('÷', '/').replace(':', '/')
        text = text.replace('\u221a', 'sqrt').replace('\u222b', 'integrate')
        text = text.replace('\u03c0', 'pi').replace('\u221e', 'oo')
        text = text.replace('\u00b2', '**2').replace('\u00b3', '**3')
        # (dikev bolme sembolleri yukarda normalize edildi)

        # Tirnaklar ve gereksiz karakterler
        text = text.replace('\u2018', '').replace('\u2019', '').replace("'", '').replace('"', '')
        text = text.replace('\n\n', '\n')

        # Context-aware OCR hata duzeltmesi
        # l/I -> 1 (kelime icinde degilse)
        text = re.sub(r'(?<![a-zA-Z])[lI](?![a-zA-Z])', '1', text)
        # o/O -> 0 (kelime icinde degilse, ancak 'log','cos' gibi fonksiyonlar haricindan)
        text = re.sub(r'(?<![a-zA-Z])[oO](?![a-zA-Z])', '0', text)
        # s/S -> 5 (kelime icinde degilse)
        text = re.sub(r'(?<![a-zA-Z])[sS](?![a-zA-Z])', '5', text)
        # Coklu bosluk temizle
        text = re.sub(r'[ \t]+', ' ', text)

        lines = text.split('\n')
        equations = [line.strip() for line in lines if line.strip()]
        return equations

    # ------------------------------------------------------------------
    # Matematik filtresi — genisletilmis
    # ------------------------------------------------------------------
    @staticmethod
    def is_actual_math(text: str) -> bool:
        stripped = text.strip()
        if len(stripped) < 2:
            return False

        # Sadece rakam(lar)dan olusan metin matematiksel ifade degil
        if re.fullmatch(r'[\d\s.]+', stripped):
            return False

        # Matematik sembolu var mi? (genisletilmis karakter kumesi)
        math_chars = re.search(
            r'[\d=+\-*/^()\[\]xyztabcnkmijpruv]|'
            r'(sin|cos|tan|log|ln|sqrt|lim|det|int|exp|abs)',
            stripped.lower()
        )
        if not math_chars:
            return False

        # Tamamen harf mi? (fonksiyon adi olmadan)
        letters_only = re.sub(r'[^a-zA-Z]', '', stripped)
        if (len(letters_only) == len(stripped) and
                not any(f in stripped.lower() for f in
                        ['sin', 'cos', 'tan', 'log', 'lim', 'det',
                         'sqrt', 'exp', 'int', 'abs', 'ln'])):
            return False

        # En az bir operator VEYA = isareti VEYA matematiksel degisken olmali
        has_operator = bool(re.search(r'[=+\-*/^]', stripped))
        has_digit    = bool(re.search(r'\d', stripped))
        has_mathfunc = any(f in stripped.lower() for f in
                           ['sin', 'cos', 'tan', 'log', 'lim', 'det',
                            'sqrt', 'exp', 'abs', 'ln', 'pi'])

        # Eger hic sayi, operator veya matematik fonksiyonu yoksa -> normal metin
        if not (has_operator or has_digit or has_mathfunc):
            return False

        return True

    # ------------------------------------------------------------------
    # Ekran bolgesinden OCR (mevcut yontem — degistirilmedi)
    # ------------------------------------------------------------------
    def _get_image_hash(self, img_array):
        return hashlib.md5(img_array.tobytes()).hexdigest()

    def extract_equations(self, bbox, use_frame_diff=False, debug=False):
        try:
            processed_img = self._preprocess_image(bbox)

            if use_frame_diff and not debug:
                current_hash = self._get_image_hash(processed_img)
                if self.last_frame_hash == current_hash:
                    return None
                self.last_frame_hash = current_hash

            # Coklu PSM ile en iyi sonucu al
            raw_text = self._extract_with_multiple_psm(processed_img)

            equations = self._parse_text_to_equations(raw_text)
            valid_equations = [eq for eq in equations if self.is_actual_math(eq)]

            # ====== DEBUG (HATA AYIKLAMA) KAYIT SISTEMI ======
            if debug:
                ts = int(time.time())
                img_path = os.path.join(OCREngine.LOG_DIR, f"debug_ocr_{ts}.png")
                log_path = os.path.join(OCREngine.LOG_DIR, f"debug_ocr_{ts}.txt")

                cv2.imwrite(img_path, processed_img)

                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f">_ OCR MOTORUNUN GORDUGU HAM METIN (RAW):\n'{raw_text}'\n\n")
                    f.write(f">_ TEMIZLEME SONRASI (PARSED):\n{equations}\n\n")
                    f.write(f">_ MATEMATIK FILTRESINDENECENLER (VALID):\n{valid_equations}\n")

            return valid_equations
        except Exception as e:
            raise OCRError(f"OCR Cikarim Hatasi: {str(e)}")

    # ------------------------------------------------------------------
    # YENI: Dosyadan gelen numpy array'den OCR
    # ------------------------------------------------------------------
    def extract_from_array(self, img_array: np.ndarray, debug=False) -> list:
        """
        DocumentEngine tarafindan kullanilir.
        Ekran yerine dosyadan gelen goruntu array'ini OCR ile tarar.
        """
        try:
            processed_img = self._preprocess_from_array(img_array)

            raw_text = self._extract_with_multiple_psm(processed_img)

            equations = self._parse_text_to_equations(raw_text)
            valid_equations = [eq for eq in equations if self.is_actual_math(eq)]

            if debug:
                ts = int(time.time())
                img_path = os.path.join(OCREngine.LOG_DIR, f"debug_array_{ts}.png")
                log_path = os.path.join(OCREngine.LOG_DIR, f"debug_array_{ts}.txt")
                cv2.imwrite(img_path, processed_img)
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f">_ RAW:\n'{raw_text}'\n\n>_ VALID:\n{valid_equations}\n")

            return valid_equations
        except Exception as e:
            raise OCRError(f"Array OCR Hatasi: {str(e)}")
