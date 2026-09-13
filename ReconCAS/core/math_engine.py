import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re

class MathError(Exception):
    pass

class UnsafeExpressionException(MathError):
    pass

class MathEngine:
    TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
    
    # | (mutlak değer sınırı) ve unicode π, ∞ de geçerli
    ALLOWED_TOKENS = re.compile(r'^[0-9a-zA-Z\.\,\+\-\*\/\^\(\)\[\]\{\}\=\>\< \t!|]+$')
    
    # V12 - Genişletilmiş Matematiksel Beyaz Liste
    SAFE_WORDS = [
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
        'Abs', 're', 'im', 'conjugate',
        # Sonsuzluk
        'oo', 'zoo',
        # Sembolik işlemler
        'limit', 'series', 'diff', 'integrate',
        'Matrix', 'det', 'trace', 'inv', 'eigenvals',
        'Eq', 'Function', 'dsolve',
        'apart', 'trigsimp', 'expand', 'simplify', 'factor'
    ]

    @staticmethod
    def _lexical_validation(text):
        clean_text = text.lower().strip()
        if not MathEngine.ALLOWED_TOKENS.match(clean_text):
            raise UnsafeExpressionException("GÜVENLİK İHLALİ: İzin verilmeyen sembol tespit edildi.")
        
        words = re.findall(r'[a-z]+', clean_text)
        for word in words:
            if word not in MathEngine.SAFE_WORDS:
                raise UnsafeExpressionException(f"GÜVENLİK İHLALİ: Tanımlanmayan fonksiyon/değişken ({word})")
        return True

    @staticmethod
    def format_input(text):
        # Temel operatör dönüşümleri
        text = text.replace('^', '**').replace(',', '.').replace('[', '(').replace(']', ')')
        # Unicode matematik sembolleri
        text = text.replace('√', 'sqrt(').replace('∫', 'integrate(')
        text = text.replace('π', 'pi').replace('∞', 'oo')
        text = text.replace('²', '**2').replace('³', '**3').replace('¹', '**1')
        text = text.replace('×', '*').replace('÷', '/')
        return text

    @staticmethod
    def is_advanced(text):
        if any(op in text for op in ['=', '>', '<']): return True
        try:
            MathEngine._lexical_validation(text)
            parsed = parse_expr(MathEngine.format_input(text), transformations=MathEngine.TRANSFORMATIONS)
            return len(parsed.free_symbols) > 0
        except: return False

    @staticmethod
    def evaluate_basic(text):
        try:
            MathEngine._lexical_validation(text)
            expr_str = MathEngine.format_input(text).replace('√', 'sqrt')
            expr_str = re.sub(r'(?<=\d)\s*[xX]\s*(?=\d)', '*', expr_str)
            expr_str = re.sub(r'(\d+)!', r'factorial(\1)', expr_str)
            
            parsed = parse_expr(expr_str, transformations=MathEngine.TRANSFORMATIONS)
            result = parsed.evalf()
            
            if result.is_integer: return int(result)
            return round(float(result), 4)
        except UnsafeExpressionException as e:
            raise e
        except Exception as e: 
            raise MathError(f"Temel Hesaplama Hatası: {str(e)}")

    @staticmethod
    def analyze_advanced(text):
        try:
            MathEngine._lexical_validation(text)
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