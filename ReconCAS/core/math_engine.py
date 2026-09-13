import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re

class MathError(Exception):
    pass

class UnsafeExpressionException(MathError):
    pass

class MathEngine:
    TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
    
    # Savunma derinliği: Standart ASCII + Unicode matematik sembolleri doğrudan kabul edilir
    ALLOWED_TOKENS = re.compile(r'^[0-9a-zA-Z\.\,\+\-\*\/\^\(\)\[\]\{\}\=\>\< \t!|π∞√∫×÷²³¹]+$')
    
    # Canonical lowercase beyaz liste (BUG-002: case-insensitive)
    SAFE_WORDS = {
        # Temel değişkenler
        'a', 'b', 'c', 'x', 'y', 'z', 't', 'f', 'g',
        'n', 'k', 'm', 'i', 'j', 'p', 'r', 'u', 'v', 'w',
        # Trigonometri
        'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
        'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
        # Matematiksel fonksiyonlar
        'log', 'ln', 'sqrt', 'pi', 'e', 'exp',
        'floor', 'ceiling', 'sign',
        # Mutlak değer ve karmaşık
        'abs', 're', 'im', 'conjugate',
        # Sonsuzluk
        'oo', 'zoo',
        # Sembolik işlemler & Matrisler
        'limit', 'series', 'diff', 'integrate',
        'matrix', 'det', 'trace', 'inv', 'eigenvals',
        'eq', 'function', 'dsolve',
        'apart', 'trigsimp', 'expand', 'simplify', 'factor', 'solve',
        # Faktöriyel ve diferansiyel belirteç
        'factorial', 'd'
    }

    @staticmethod
    def format_input(text: str) -> str:
        """
        Ham matematiksel metni SymPy uyumlu formata normalize eder.
        Syntax-aware (kök, integral, mutlak değer, çarpan operatörleri).
        """
        if not text:
            return ""

        # Tire varyantlarını standart eksiye çevir
        text = text.replace('—', '-').replace('–', '-').replace('−', '-')
        
        # Unicode matematik operatörleri
        text = text.replace('×', '*').replace('÷', '/')
        text = text.replace('π', 'pi').replace('∞', 'oo')
        text = text.replace('²', '**2').replace('³', '**3').replace('¹', '**1')
        text = text.replace('^', '**')

        # Köşeli parantezleri yuvarlak paranteze çevir (Matris listeleri hariç tekli kullanım)
        if '[[' not in text and ']]' not in text:
            text = text.replace('[', '(').replace(']', ')')

        # Ondalık virgülü noktaya çevir (sadece rakamlar arasındaysa: ör. 3,14 -> 3.14)
        # Parametre virgüllerini (diff(x, x), Matrix([[1, 2]])) korur!
        text = re.sub(r'(\d+),(\d+)', r'\1.\2', text)

        # BUG-016: Mutlak değer syntax desteği |expr| -> Abs(expr)
        text = re.sub(r'\|([^|]+)\|', r'Abs(\1)', text)

        # BUG-002: SymPy'nin büyük harfle beklediği sınıfların canonical normalizasyonu
        text = re.sub(r'\bmatrix\b', 'Matrix', text, flags=re.IGNORECASE)
        text = re.sub(r'\babs\b', 'Abs', text, flags=re.IGNORECASE)
        text = re.sub(r'\beq\b', 'Eq', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfunction\b', 'Function', text, flags=re.IGNORECASE)

        # BUG-003: Syntax-aware karekök (√) dönüşümü
        # 1) √(x+1) veya √{x+1}
        text = re.sub(r'√\s*\(([^)]+)\)', r'sqrt(\1)', text)
        text = re.sub(r'√\s*\{([^}]+)\}', r'sqrt(\1)', text)
        # 2) √x veya √16 gibi tekli belirteçler
        text = re.sub(r'√\s*([a-zA-Z0-9_]+)', r'sqrt(\1)', text)
        # 3) Kalan açık √ varsa genel sqrt ekle
        text = text.replace('√', 'sqrt')

        # BUG-003: Syntax-aware integral (∫) dönüşümü
        # 1) ∫ expr dx veya ∫ (expr) dx
        text = re.sub(r'∫\s*\((.+?)\)\s*d([a-zA-Z])', r'integrate(\1, \2)', text)
        text = re.sub(r'∫\s*(.+?)\s*d([a-zA-Z])(?=\s*[+\-*/=]|$)', r'integrate(\1, \2)', text)
        # 2) ∫ expr (belirteçsiz: varsayılan x'e göre)
        text = re.sub(r'∫\s*\((.+?)\)', r'integrate(\1, x)', text)
        text = re.sub(r'∫\s*([a-zA-Z0-9_+*/^-]+)', r'integrate(\1, x)', text)
        text = text.replace('∫', 'integrate')

        # Sayılar arasındaki 'x' çarpma işaretini '*' yap (ör. 5 x 3 -> 5 * 3)
        text = re.sub(r'(?<=\d)\s*[xX]\s*(?=\d)', '*', text)

        # Faktöriyel dönüşümü (ör. 12! -> factorial(12), n! -> factorial(n))
        text = re.sub(r'(\d+)!', r'factorial(\1)', text)
        text = re.sub(r'([a-zA-Z])!', r'factorial(\1)', text)

        return text.strip()

    @staticmethod
    def _lexical_validation(text: str) -> bool:
        """
        Zero-Trust Lexical Parser: Beyaz listede olmayan karakter ve fonksiyonları engeller.
        """
        clean_text = text.strip()
        if not MathEngine.ALLOWED_TOKENS.match(clean_text):
            raise UnsafeExpressionException("GÜVENLİK İHLALİ: İzin verilmeyen sembol tespit edildi.")
        
        # Kelimeleri ayıkla ve canonical lowercase ile kontrol et (BUG-002)
        words = re.findall(r'[a-zA-Z]+', clean_text.lower())
        for word in words:
            if word not in MathEngine.SAFE_WORDS:
                raise UnsafeExpressionException(f"GÜVENLİK İHLALİ: Tanımlanmayan fonksiyon/değişken ({word})")
        return True

    @staticmethod
    def validate_expression(text: str) -> tuple:
        """
        BUG-007: OCR çıktısını SymPy ile doğrular.
        Pipeline: Normalization -> Lexical Validation -> SymPy Parser
        Returns: (is_valid: bool, formatted_text: str, parsed_object: Any, error_msg: str | None)
        """
        if not text or not text.strip():
            return False, "", None, "Boş ifade"
        try:
            formatted = MathEngine.format_input(text)
            MathEngine._lexical_validation(formatted)

            # Denklem mi kontrolü
            if '=' in formatted:
                parts = formatted.split('=', 1)
                left_str = parts[0].strip()
                right_str = parts[1].strip()
                if not left_str or not right_str:
                    return False, formatted, None, "Eksik denklem tarafı"
                left = parse_expr(left_str, transformations=MathEngine.TRANSFORMATIONS)
                right = parse_expr(right_str, transformations=MathEngine.TRANSFORMATIONS)
                eq_obj = sp.Eq(left, right)
                return True, formatted, eq_obj, None
            else:
                parsed = parse_expr(formatted, transformations=MathEngine.TRANSFORMATIONS)
                return True, formatted, parsed, None
        except UnsafeExpressionException as e:
            return False, text, None, f"Güvenlik ihlali: {e}"
        except Exception as e:
            return False, text, None, f"Sözdizimi hatası: {e}"

    @staticmethod
    def is_advanced(text: str) -> bool:
        if any(op in text for op in ['=', '>', '<']):
            return True
        try:
            formatted = MathEngine.format_input(text)
            MathEngine._lexical_validation(formatted)
            parsed = parse_expr(formatted, transformations=MathEngine.TRANSFORMATIONS)
            return len(parsed.free_symbols) > 0
        except Exception:
            return False

    @staticmethod
    def evaluate_basic(text: str):
        """
        Temel aritmetik ifadeleri hesaplar (sayısal çıktı).
        """
        try:
            # BUG-001: Önce normalizasyon, sonra validasyon
            formatted = MathEngine.format_input(text)
            MathEngine._lexical_validation(formatted)
            
            parsed = parse_expr(formatted, transformations=MathEngine.TRANSFORMATIONS)
            if hasattr(parsed, 'doit'):
                parsed = parsed.doit()
            result = parsed.evalf()
            
            if result.is_integer:
                return int(result)
            return round(float(result), 4)
        except UnsafeExpressionException as e:
            raise e
        except Exception as e: 
            raise MathError(f"Temel Hesaplama Hatası: {str(e)}")

    @staticmethod
    def analyze_advanced(text: str):
        """
        Sembolik analiz ve denklem çözme.
        """
        try:
            # BUG-001: Önce normalizasyon, sonra validasyon
            formatted = MathEngine.format_input(text)
            MathEngine._lexical_validation(formatted)
            
            if '=' in formatted:
                parts = formatted.split('=', 1)
                left = parse_expr(parts[0], transformations=MathEngine.TRANSFORMATIONS)
                right = parse_expr(parts[1], transformations=MathEngine.TRANSFORMATIONS)
                diff_expr = left - right
                roots = sp.solve(sp.Eq(left, right))
                return True, diff_expr, roots
            else:
                parsed = parse_expr(formatted, transformations=MathEngine.TRANSFORMATIONS)
                if hasattr(parsed, 'doit'):
                    parsed = parsed.doit()
                return False, sp.simplify(parsed), None
        except UnsafeExpressionException as e:
            raise e
        except Exception as e:
            raise MathError(f"Sembolik Analiz Hatası: {str(e)}")

    @staticmethod
    def dispatch_operation(text: str) -> dict:
        """
        BUG-015: Girdideki özel sembolik operasyonu tespit edip birinci sınıf işlem olarak çalıştırır.
        """
        formatted = MathEngine.format_input(text)
        MathEngine._lexical_validation(formatted)
        
        if '=' in formatted:
            parts = formatted.split('=', 1)
            left = parse_expr(parts[0], transformations=MathEngine.TRANSFORMATIONS)
            right = parse_expr(parts[1], transformations=MathEngine.TRANSFORMATIONS)
            diff_expr = left - right
            roots = sp.solve(sp.Eq(left, right))
            return {
                "op": "SOLVE",
                "equation": f"{left} = {right}",
                "standard_form": f"{diff_expr} = 0",
                "result": roots
            }
        
        parsed = parse_expr(formatted, transformations=MathEngine.TRANSFORMATIONS)
        if hasattr(parsed, 'doit'):
            evaluated = parsed.doit()
            return {
                "op": parsed.__class__.__name__.upper(),
                "expression": parsed,
                "result": evaluated
            }
        
        simplified = sp.simplify(parsed)
        return {
            "op": "SIMPLIFY",
            "expression": parsed,
            "result": simplified
        }