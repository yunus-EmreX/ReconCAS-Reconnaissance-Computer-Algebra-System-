from PIL import Image, ImageGrab, ImageEnhance
import pytesseract
import re
import hashlib

# Tesseract'ın sistemdeki konumunu tanımla
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- ÖZEL HATA SINIFLARI ---
class OCRError(Exception):
    """OCR Tarama ve Görüntü İşleme Hataları"""
    pass

class OCREngine:
    def __init__(self):
        # Frame Differencing (Görüntü Farklılaştırma) için önceki karenin hash'ini tutar
        self.last_frame_hash = None

    @staticmethod
    def enhance_image(img, is_full_screen=False):
        """Karakterlerin tanınabilirliğini artırmak için filtreler uygular"""
        try:
            width, height = img.size
            scale = 1.2 if is_full_screen else 2.0
            resample_mode = Image.Resampling.BILINEAR if is_full_screen else Image.Resampling.BICUBIC
            
            img = img.resize((int(width * scale), int(height * scale)), resample_mode).convert('L')
            
            if not is_full_screen:
                img = ImageEnhance.Sharpness(img).enhance(2.0)
            
            img = ImageEnhance.Contrast(img).enhance(1.5)
            return img
        except Exception as e:
            raise OCRError(f"Görüntü İşleme Hatası: {e}")

    def _generate_frame_hash(self, img) -> str:
        """Resmin piksellerini okuyup ona özel bir kimlik (hash) üretir"""
        return hashlib.md5(img.tobytes()).hexdigest()

    def extract_equations(self, bbox, is_full_screen=False, use_frame_diff=False):
        """Ekrandan metni süzer, frame_diff True ise değişmeyen ekranlarda OCR'ı atlar"""
        try:
            img = ImageGrab.grab(bbox=bbox)
            
            # FRAME DIFFERENCING (Canlı Tarama Optimizasyonu)
            if use_frame_diff:
                current_hash = self._generate_frame_hash(img)
                if current_hash == self.last_frame_hash:
                    img.close()
                    # Ekran değişmemiş, None dön ki sistem işlemciyi yormasın
                    return None 
                self.last_frame_hash = current_hash

            enhanced_img = self.enhance_image(img, is_full_screen)
            
            psm_config = '--psm 3' if is_full_screen else '--psm 6'
            text = pytesseract.image_to_string(enhanced_img, config=psm_config).strip()
            
            # RAM Sızıntısı (Memory Leak) engelleme
            img.close()
            enhanced_img.close()
            
            if not text: 
                return []
            
            return self._parse_text_to_equations(text)
            
        except Exception as e:
            raise OCRError(f"Ekran Yakalama Hatası: {e}")

    @staticmethod
    def _parse_text_to_equations(text):
        """OCR'ın okuduğu metni temizler, akıllı düzeltmeler yapar ve satırlara ayırır"""
        
        # 1. TEMEL OPERATÖR DÜZELTMELERİ
        text = re.sub(r'[—–_~−]', '-', text)
        text = text.replace('×', '*').replace('÷', '/').replace(':', '/')
        
        # 2. AKILLI MATEMATİKSEL DÜZELTİCİ (BTK Madde 25)
        # sin, cos, log, tan gibi kelimelerin bozulmaması için büyük harf I ve O direkt çevrilir (fonksiyonlarda büyük harf olmaz)
        text = text.replace('I', '1').replace('O', '0')
        
        # Sadece tek başına duran veya sayılara yapışık küçük 'l' ve 'o' harflerini rakama çevirir. 
        # Böylece 'log' veya 'cos' kelimeleri ZARAR GÖRMEZ!
        text = re.sub(r'(?<![a-zA-Z])l(?![a-zA-Z])', '1', text) # Tek başına l -> 1
        text = re.sub(r'(?<![a-zA-Z])o(?![a-zA-Z])', '0', text) # Tek başına o -> 0
        
        lines = text.split('\n')
        equations = []
        current_expr = ""
        
        for line in lines:
            line = line.strip()
            if not line or re.match(r'^[\-=]{2,}$', line.replace(' ', '')): 
                continue
            
            # Eğer satır +, -, * ile başlıyorsa bir önceki satırın devamıdır
            if re.match(r'^[+\-\*/]', line) and current_expr:
                current_expr += " " + line
            else:
                if current_expr: 
                    equations.append(current_expr)
                current_expr = line
                
        if current_expr: 
            equations.append(current_expr)
            
        return equations

    @staticmethod
    def is_actual_math(text):
        """Okunan metin sadece düz yazı mı yoksa matematiğe mi benziyor kontrol eder"""
        clean = text.replace(" ", "")
        
        # Sadece sayılardan ibaretse atla
        if re.fullmatch(r'\-?\d+(\.\d+)?', clean): 
            return False 
        
        # İçinde herhangi bir operatör veya değişken varsa bu matematiktir
        if not re.search(r'[+\-\*/xXyYzZ√!C\(\)=><]', text): 
            return False
            
        return True