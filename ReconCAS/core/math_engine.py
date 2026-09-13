import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re

# --- ÖZEL HATA SINIFLARI ---
class MathError(Exception):
    """Matematiksel analiz ve hesaplama hataları"""
    pass

class UnsafeExpressionException(MathError):
    """Zararlı kod enjeksiyonu veya izin verilmeyen karakter tespiti"""
    pass

class MathEngine:
    TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
    
    # BEYAZ LİSTE (WHITELIST) FİLTRESİ: Yalnızca matematiğe dair şeylere izin verilir.
    ALLOWED_TOKENS = re.compile(r'^[0-9a-zA-Z\.\,\+\-\*\/\^\(\)\[\]\{\}\=\>\< \t!]+$')
    SAFE_WORDS = ['x', 'y', 'z', 'sin', 'cos', 'tan', 'log', 'sqrt', 'pi', 'e', 'exp']

    @staticmethod
    def _lexical_validation(text):
        """Gelen verinin %100 saf matematik olduğundan emin olur."""
        clean_text = text.lower().strip()
        
        # 1. Karakter Kontrolü
        if not MathEngine.ALLOWED_TOKENS.match(clean_text):
            raise UnsafeExpressionException("GÜVENLİK İHLALİ: İzin verilmeyen sembol tespit edildi.")
        
        # 2. Kelime Kontrolü (Zararlı Python komutlarını engeller)
        words = re.findall(r'[a-z]+', clean_text)
        for word in words:
            if word not in MathEngine.SAFE_WORDS:
                raise UnsafeExpressionException(f"GÜVENLİK İHLALİ: Tanımlanmayan fonksiyon/değişken ({word})")
        return True

    @staticmethod
    def format_input(text):
        return text.replace('^', '**').replace(',', '.').replace('[', '(').replace(']', ')')

    @staticmethod
    def is_advanced(text):
        if any(op in text for op in ['=', '>', '<']): return True
        try:
            MathEngine._lexical_validation(text) # Güvenlik taraması
            parsed = parse_expr(MathEngine.format_input(text), transformations=MathEngine.TRANSFORMATIONS)
            return len(parsed.free_symbols) > 0
        except: return False

    @staticmethod
    def evaluate_basic(text):
        try:
            MathEngine._lexical_validation(text) # Güvenlik taraması
            expr_str = MathEngine.format_input(text).replace('x', '*').replace('X', '*').replace('√', 'sqrt')
            expr_str = re.sub(r'(\d+)!', r'factorial(\1)', expr_str)
            
            parsed = parse_expr(expr_str, transformations=MathEngine.TRANSFORMATIONS)
            result = parsed.evalf()
            
            if result.is_integer: return int(result)
            return round(float(result), 4)
        except UnsafeExpressionException as e:
            raise e # Güvenlik hatasını direkt fırlat
        except Exception as e: 
            raise MathError(f"Temel Hesaplama Hatası: {str(e)}")

    @staticmethod
    def analyze_advanced(text):
        try:
            MathEngine._lexical_validation(text) # Güvenlik taraması
            expr_str = MathEngine.format_input(text)
            
            if '=' in expr_str:
                parts = expr_str.split('=', 1)
                left = parse_expr(parts[0], transformations=MathEngine.TRANSFORMATIONS)
                right = parse_expr(parts[1], transformations=MathEngine.TRANSFORMATIONS)
                return True, left - right, sp.solve(sp.Eq(left, right))
            else:
                return False, sp.simplify(parse_expr(expr_str, transformations=MathEngine.TRANSFORMATIONS)), None
        except UnsafeExpressionException as e:
            raise e
        except Exception as e:
            raise MathError(f"Sembolik Analiz Hatası: {str(e)}")