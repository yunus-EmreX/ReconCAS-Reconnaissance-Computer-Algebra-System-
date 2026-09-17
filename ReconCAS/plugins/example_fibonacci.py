# -*- coding: utf-8 -*-
"""
ReconCAS Plugin: Fibonacci Hesaplayici
Bu dosya, plugin sisteminin nasil calistigini gosteren ornek bir plugin'dir.
"""

PLUGIN_NAME = "Fibonacci Hesaplayici"
PLUGIN_VERSION = "1.0"
PLUGIN_DESCRIPTION = "Verilen N sayisi icin Fibonacci dizisinin ilk N elemanini hesaplar."

def execute(input_text: str) -> str:
    """Plugin'in ana fonksiyonu. Girdi alir, cikti dondurur."""
    try:
        n = int(input_text.strip())
        if n <= 0:
            return "Lutfen pozitif bir tam sayi girin."
        if n > 100:
            return "Maksimum 100 eleman desteklenir."
        
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[-1] + fib[-2])
        
        result = fib[:n]
        return f"Fibonacci({n}): {result}"
    except ValueError:
        return "Hata: Gecerli bir tam sayi girin (ornek: 10)"
