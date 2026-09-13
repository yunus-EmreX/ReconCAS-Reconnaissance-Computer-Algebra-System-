import pytesseract
from PIL import ImageGrab, Image
import cv2
import numpy as np
import hashlib
import re
import os
import time

# Tesseract'ın kurulu olduğu dizin
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRError(Exception):
    pass

class OCREngine:
    def __init__(self):
        self.last_frame_hash = None
        # Log klasörünü GÜVENLİ bir şekilde oluştur
        try:
            if not os.path.exists("logs"):
                os.makedirs("logs", exist_ok=True)
        except Exception as e:
            print(f">_ [UYARI] Log klasörü oluşturulamadı. Windows izni reddetti: {e}")
            

    def _get_image_hash(self, img_array):
        return hashlib.md5(img_array.tobytes()).hexdigest()

    def _preprocess_image(self, bbox):
        try:
            pil_img = ImageGrab.grab(bbox)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            pad = 30
            img = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            if np.mean(gray) < 127:
                gray = cv2.bitwise_not(gray)
            
            height, width = gray.shape
            if height < 40:
                gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
                
            return gray
        except Exception as e:
            raise OCRError(f"Görüntü işleme hatası: {str(e)}")

    @staticmethod
    def _parse_text_to_equations(text):
        if not text or not text.strip():
            return []
        text = re.sub(r'[—–_~−]', '-', text)
        text = text.replace('×', '*').replace('÷', '/').replace(':', '/')
        text = text.replace('‘', '').replace('’', '').replace('\'', '').replace('"', '')
        text = text.replace('\n\n', '\n')
        text = re.sub(r'(?<![a-zA-Z])[lI](?![a-zA-Z])', '1', text) 
        text = re.sub(r'(?<![a-zA-Z])[oO](?![a-zA-Z])', '0', text) 
        text = re.sub(r'(?<![a-zA-Z])[sS](?![a-zA-Z])', '5', text) 
        text = re.sub(r'[ \t]+', ' ', text)

        lines = text.split('\n')
        equations = [line.strip() for line in lines if line.strip()]
        return equations

    @staticmethod
    def is_actual_math(text):
        if not re.search(r'[\dxyztabAB=+\-*/^()]', text.lower()):
            return False
        letters_only = re.sub(r'[^a-zA-Z]', '', text)
        if len(letters_only) == len(text) and not any(f in text.lower() for f in ['sin', 'cos', 'tan', 'log', 'lim', 'det']):
            return False
        return True

    def extract_equations(self, bbox, use_frame_diff=False, debug=False):
        try:
            processed_img = self._preprocess_image(bbox)

            if use_frame_diff and not debug: # Debug açıksa frame differencing iptal, her şeyi kaydet
                current_hash = self._get_image_hash(processed_img)
                if self.last_frame_hash == current_hash:
                    return None
                self.last_frame_hash = current_hash

            custom_config = r'--oem 3 --psm 6'
            raw_text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            equations = self._parse_text_to_equations(raw_text)
            valid_equations = [eq for eq in equations if self.is_actual_math(eq)]
            
            # ====== DEBUG (HATA AYIKLAMA) KAYIT SİSTEMİ ======
            if debug:
                ts = int(time.time())
                img_path = f"logs/debug_ocr_{ts}.png"
                log_path = f"logs/debug_ocr_{ts}.txt"
                
                # 1. Tesseract'ın gördüğü resmi kaydet (Acaba bembeyaz mı oldu?)
                cv2.imwrite(img_path, processed_img)
                
                # 2. Tesseract'ın okuduğu ham metni ve filtreden geçenleri kaydet
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f">_ OCR MOTORUNUN GÖRDÜĞÜ HAM METİN (RAW):\n'{raw_text}'\n\n")
                    f.write(f">_ TEMİZLEME SONRASI (PARSED):\n{equations}\n\n")
                    f.write(f">_ MATEMATİK FİLTRESİNDEN GEÇENLER (VALID):\n{valid_equations}\n")
            
            return valid_equations
        except Exception as e:
            raise OCRError(f"OCR Çıkarım Hatası: {str(e)}")