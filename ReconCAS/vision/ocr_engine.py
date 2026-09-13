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
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img.copy()

        # Karanlik Mod Koruyucu: ortalama < 127 ise rengi ters cevir
        if np.mean(gray) < 127:
            gray = cv2.bitwise_not(gray)

        # Adaptif olcekleme: hedef yukseklik 96px (kucuk gorselleri buyut, ama sayfa gorselini yok etme)
        h, w = gray.shape
        target_h = 96
        if h < target_h and h > 0:
            scale = target_h / h
            gray = cv2.resize(gray, None, fx=scale, fy=scale,
                               interpolation=cv2.INTER_CUBIC)

        # OTSU ikili esikleme: gurultuyu temizler, karakterleri keskinlestirir
        _, binary = cv2.threshold(gray, 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Hafif dilate: ince yazilari kalinlastirir (Tesseract icin faydali)
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)

        return binary

    # ------------------------------------------------------------------
    # BUG-008 & BUG-009: Sayfa bolge ve satir tespiti
    # ------------------------------------------------------------------
    @staticmethod
    def segment_into_line_regions(img_array: np.ndarray) -> list:
        """
        Sayfa olcegindeki dokumanlari yatay satir bolgelerine ayirir.
        Tum sayfayi kucultmek yerine, her satiri bagimsiz cozunurlukte kirpar.
        """
        if img_array.ndim == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array.copy()

        h, w = gray.shape
        if h < 300:
            return [((0, 0, w, h), img_array)]

        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        # Yatay genis kernel ile satir ici karakterleri birlestir
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        regions = []
        for c in contours:
            rx, ry, rw, rh = cv2.boundingRect(c)
            if rh >= 14 and rw >= 25:
                pad = 10
                y1 = max(0, ry - pad)
                y2 = min(h, ry + rh + pad)
                x1 = max(0, rx - pad)
                x2 = min(w, rx + rw + pad)
                crop = img_array[y1:y2, x1:x2]
                regions.append(((x1, y1, x2 - x1, y2 - y1), crop))

        regions.sort(key=lambda r: r[0][1])
        return regions if regions else [((0, 0, w, h), img_array)]

    # ------------------------------------------------------------------
    # BUG-004 & BUG-010: Coklu PSM modunda OCR ve guven skoru
    # ------------------------------------------------------------------
    @classmethod
    def _extract_with_multiple_psm(cls, img: np.ndarray) -> tuple:
        """
        PSM 6, 11, 4 dener. Cok kriterli skorlama ile en gecerli sonucu secer.
        Returns: (best_text, best_confidence)
        """
        from core.math_engine import MathEngine
        psm_modes = ['--oem 3 --psm 6', '--oem 3 --psm 11', '--oem 3 --psm 4']
        best_text = ""
        best_score = -999.0
        best_conf = 50.0

        for config in psm_modes:
            try:
                data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
                confs = []
                for i in range(len(data['text'])):
                    w = data['text'][i].strip()
                    c = float(data['conf'][i])
                    if w and c >= 0:
                        confs.append(c)

                text = pytesseract.image_to_string(img, config=config)
                if not text.strip():
                    continue

                avg_conf = (sum(confs) / len(confs)) if confs else 50.0
                c_score = avg_conf / 100.0

                eqs = cls._parse_text_to_equations(text)
                valid_count = 0
                for eq in eqs:
                    is_val, _, _, _ = MathEngine.validate_expression(eq)
                    if is_val:
                        valid_count += 1
                    else:
                        _, was_corr = cls.correct_ocr_confusion(eq)
                        if was_corr:
                            valid_count += 1

                parse_score = (valid_count / len(eqs)) if eqs else 0.0

                # Parantez dengesi ve ardisik operator kontrolu
                balanced = (text.count('(') == text.count(')')) and (text.count('[') == text.count(']'))
                has_repeated_ops = bool(re.search(r'[+\-*/=]{3,}', text))
                structure_score = (0.6 if balanced else 0.1) + (0.4 if not has_repeated_ops else 0.0)

                math_chars = len(re.findall(r'[\d+\-*/=^()\[\]xyztabcnkmijpruv]', text.lower()))
                math_score = min(1.0, math_chars / max(len(text.strip()), 1))

                # Dogal dil kelime cezasi (BUG-004 & BUG-005)
                bad_words = [w for w in re.findall(r'[a-zA-Z]{4,}', text.lower()) if w not in MathEngine.SAFE_WORDS]
                garbage_penalty = min(1.0, len(bad_words) * 0.25)

                score = (
                    c_score * 0.30
                    + parse_score * 0.30
                    + structure_score * 0.20
                    + math_score * 0.15
                    - garbage_penalty * 0.25
                )

                if score > best_score:
                    best_score = score
                    best_text = text
                    best_conf = avg_conf

            except Exception:
                continue

        return best_text, best_conf

    # ------------------------------------------------------------------
    # BUG-PDF-007: Coklu denklem bolumleme
    # ------------------------------------------------------------------
    @staticmethod
    def _segment_line_into_equations(line: str) -> list:
        """
        Bir satirda yan yana duran coklu denklemleri ayiklar.
        Ornek: 'x+0=1 ly-3=9' -> ['x+0=1', 'ly-3=9']
        """
        line = line.strip()
        if not line:
            return []

        if line.count('=') > 1:
            parts = re.split(r'(?<=[0-9a-zA-Z)])\s{2,}(?=[a-zA-Z])|(?<=[0-9])\s+(?=[a-zA-Z][a-zA-Z0-9_]*\s*[-+=*])', line)
            if len(parts) > 1:
                return [p.strip() for p in parts if p.strip()]
        return [line]

    # ------------------------------------------------------------------
    # Metin -> denklem listesi donusumu
    # ------------------------------------------------------------------
    @classmethod
    def _parse_text_to_equations(cls, text: str) -> list:
        if not text or not text.strip():
            return []

        # Unicode matematik sembolleri normalize et
        text = text.replace('—', '-').replace('–', '-').replace('−', '-')
        text = re.sub(r'[_~]', '-', text)
        text = text.replace('×', '*').replace('÷', '/').replace(':', '/')
        text = text.replace('\u221a', 'sqrt').replace('\u222b', 'integrate')
        text = text.replace('\u03c0', 'pi').replace('\u221e', 'oo')
        text = text.replace('\u00b2', '**2').replace('\u00b3', '**3')
        text = text.replace('\u2018', '').replace('\u2019', '').replace("'", '').replace('"', '')
        text = text.replace('\n\n', '\n')

        # Context-aware OCR hata duzeltmesi
        text = re.sub(r'(?<![a-zA-Z])[lI](?![a-zA-Z])', '1', text)
        text = re.sub(r'(?<![a-zA-Z])[oO](?![a-zA-Z])', '0', text)
        text = re.sub(r'(?<![a-zA-Z])[sS](?![a-zA-Z])', '5', text)
        text = re.sub(r'[ \t]+', ' ', text)

        lines = text.split('\n')
        equations = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            sub_eqs = cls._segment_line_into_equations(line_str)
            for sub_eq in sub_eqs:
                if sub_eq.strip():
                    equations.append(sub_eq.strip())
        return equations

    # ------------------------------------------------------------------
    # BUG-006 & BUG-PDF-001..006: Token bazli confusion duzeltme
    # ------------------------------------------------------------------
    @staticmethod
    def correct_ocr_confusion(eq: str) -> tuple:
        """
        Token bazli OCR hata duzeltmesi.
        ly+5=2 -> y+5=2
        lx-4=3 -> x-4=3
        Ix-4=3 -> x-4=3
        Returns: (corrected_equation, is_valid)
        """
        from core.math_engine import MathEngine
        eq_clean = eq.strip()
        
        is_val, _, _, _ = MathEngine.validate_expression(eq_clean)
        if is_val:
            return eq_clean, True
            
        candidates = [eq_clean]
        
        cand_strip_start = re.sub(r'^[lI]([a-zA-Z])', r'\1', eq_clean)
        if cand_strip_start != eq_clean:
            candidates.append(cand_strip_start)
            
        cand_num_start = re.sub(r'^[lI]([a-zA-Z])', r'1*\1', eq_clean)
        if cand_num_start != eq_clean:
            candidates.append(cand_num_start)
            
        cand_mid = re.sub(r'(?<=[=+\-*/\s])[lI]([a-zA-Z])', r'\1', eq_clean)
        if cand_mid != eq_clean:
            candidates.append(cand_mid)
            
        cand_clean_end = re.sub(r'(\d+)[A-Z]$', r'\1', eq_clean)
        if cand_clean_end != eq_clean:
            candidates.append(cand_clean_end)
            
        cand_digits = re.sub(r'(?<=\d)[lIi](?=\d)', '1', eq_clean)
        cand_digits = re.sub(r'(?<=[=+\-*/])[lIi](?=\d)', '1', cand_digits)
        if cand_digits != eq_clean:
            candidates.append(cand_digits)
            candidates.append(re.sub(r'^[lI]([a-zA-Z])', r'\1', cand_digits))

        for cand in candidates:
            is_valid, _, _, _ = MathEngine.validate_expression(cand)
            if is_valid:
                return cand, True

        return eq_clean, False

    # ------------------------------------------------------------------
    # BUG-005: Matematik filtresi (False-Positive Ayiklayici)
    # ------------------------------------------------------------------
    @classmethod
    def is_actual_math(cls, text: str) -> bool:
        if not text or not text.strip():
            return False
        stripped = text.strip()
        if len(stripped) < 2:
            return False

        # Sadece rakam(lar)dan olusan metin elenir (or. '15', '3.14')
        if re.fullmatch(r'[\d\s.]+', stripped):
            return False

        # Sarkan gecersiz operatorler (or. '=8', 'ly-', '+5=')
        if stripped.startswith('=') or stripped.endswith(('=', '-', '+', '*', '/')):
            return False

        # Dogal dil elemesi (or. 'crore/ serine iar', 'hello / world')
        from core.math_engine import MathEngine
        alpha_words = re.findall(r'[a-zA-Z]{3,}', stripped.lower())
        non_safe_words = [w for w in alpha_words if w not in MathEngine.SAFE_WORDS]
        has_digit = bool(re.search(r'\d', stripped))
        if len(non_safe_words) >= 2 and not has_digit:
            return False

        if len(non_safe_words) >= 1 and not has_digit and not any(op in stripped for op in ['=', '+', '-', '*', '^']):
            return False

        letters_only = re.sub(r'[^a-zA-Z]', '', stripped)
        if len(letters_only) == len(stripped):
            if not any(f in stripped.lower() for f in ['sin', 'cos', 'tan', 'log', 'ln', 'sqrt', 'exp', 'abs', 'lim', 'det', 'diff', 'int']):
                return False

        has_op = bool(re.search(r'[=+\-*/^]', stripped))
        has_mathfunc = any(f in stripped.lower() for f in ['sin', 'cos', 'tan', 'log', 'ln', 'sqrt', 'exp', 'abs', 'lim', 'det', 'pi', 'oo'])
        if not (has_op or has_mathfunc):
            return False

        is_val, _, _, _ = MathEngine.validate_expression(stripped)
        if is_val:
            return True

        # Token confusion ile duzeltilebilen ifadeler gecerlidir
        _, was_corrected = cls.correct_ocr_confusion(stripped)
        if was_corrected:
            return True

        return False

    # ------------------------------------------------------------------
    # Ekran bolgesinden OCR
    # ------------------------------------------------------------------
    def _get_image_hash(self, img_array):
        return hashlib.md5(img_array.tobytes()).hexdigest()

    def extract_equations(self, bbox, use_frame_diff=False, debug=False, return_details=False):
        try:
            processed_img = self._preprocess_image(bbox)

            if use_frame_diff and not debug:
                current_hash = self._get_image_hash(processed_img)
                if self.last_frame_hash == current_hash:
                    return None
                self.last_frame_hash = current_hash

            raw_text, conf = self._extract_with_multiple_psm(processed_img)
            equations = self._parse_text_to_equations(raw_text)

            valid_items = []
            for eq in equations:
                if not self.is_actual_math(eq):
                    continue
                corrected, is_val = self.correct_ocr_confusion(eq)
                item = {
                    "raw_text": eq,
                    "normalized_text": eq,
                    "equation": corrected if is_val else eq,
                    "confidence": round(conf, 1),
                    "is_valid": is_val
                }
                valid_items.append(item)

            if debug:
                ts = int(time.time())
                img_path = os.path.join(OCREngine.LOG_DIR, f"debug_ocr_{ts}.png")
                log_path = os.path.join(OCREngine.LOG_DIR, f"debug_ocr_{ts}.txt")
                cv2.imwrite(img_path, processed_img)
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f">_ OCR RAW:\n'{raw_text}'\n\n>_ PARSED:\n{equations}\n\n>_ ITEMS:\n{valid_items}\n")

            if return_details:
                return valid_items
            return [it["equation"] for it in valid_items]

        except Exception as e:
            raise OCRError(f"OCR Cikarim Hatasi: {str(e)}")

    # ------------------------------------------------------------------
    # BUG-011: Dosyadan gelen numpy array'den OCR (Zengin veri modeli)
    # ------------------------------------------------------------------
    def extract_from_array(self, img_array: np.ndarray, debug=False, return_details=True) -> list:
        """
        DocumentEngine tarafindan kullanilir.
        Sayfa olcegindeki gorseli satir bolgelerine ayirip yuksek dogrulukla OCR yapar.
        """
        try:
            regions = self.segment_into_line_regions(img_array)
            all_items = []

            for (rx, ry, rw, rh), crop in regions:
                processed_crop = self._preprocess_from_array(crop)
                raw_text, conf = self._extract_with_multiple_psm(processed_crop)
                if not raw_text.strip():
                    continue

                equations = self._parse_text_to_equations(raw_text)
                for eq in equations:
                    if not self.is_actual_math(eq):
                        continue
                    corrected, is_val = self.correct_ocr_confusion(eq)
                    item = {
                        "raw_text": eq,
                        "normalized_text": eq,
                        "equation": corrected if is_val else eq,
                        "confidence": round(conf, 1),
                        "is_valid": is_val
                    }
                    all_items.append(item)

            if debug:
                ts = int(time.time())
                img_path = os.path.join(OCREngine.LOG_DIR, f"debug_array_{ts}.png")
                log_path = os.path.join(OCREngine.LOG_DIR, f"debug_array_{ts}.txt")
                cv2.imwrite(img_path, img_array)
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f">_ REGIONS: {len(regions)}\n>_ ITEMS:\n{all_items}\n")

            if return_details:
                return all_items
            return [it["equation"] for it in all_items]

        except Exception as e:
            raise OCRError(f"Array OCR Hatasi: {str(e)}")
