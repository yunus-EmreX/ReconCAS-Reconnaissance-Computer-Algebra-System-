import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Fallback imports in case modules don't exist yet for testing
try:
    from vision.ocr_engine import OCREngine
except ImportError:
    class OCREngine:
        PREPROCESS_PADDING = 30
        TARGET_HEIGHT = 96
        DARK_MODE_THRESHOLD = 127
        MIN_CONTOUR_HEIGHT = 14
        MIN_CONTOUR_WIDTH = 25
        MORPH_KERNEL_W = 40
        MORPH_KERNEL_H = 5

try:
    from core.math_engine import MathEngine
except ImportError:
    class MathEngine:
        SAFE_WORDS = {"sin", "cos", "tan", "log", "sqrt"}
        @staticmethod
        def format_input(expr):
            return expr.strip()
        @staticmethod
        def _lexical_validation(expr):
            if "error" in expr:
                return False, "Invalid syntax"
            return True, "OK"

class OCRCalibratorPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        self.bg = "#0d111a"
        self.fg = "#00FF41"
        self.accent = "#00E5FF"
        self.gold = "#FFD700"
        self.error = "#FF003C"
        self.card_bg = "#111624"
        self.border = "#202636"
        self.font_body = ("Consolas", 9)
        self.font_header = ("Consolas", 10, "bold")
        
        self.sliders = {}
        
        self.build()

    def build(self):
        self.parent.configure(bg=self.bg)
        
        # Section 1: OCR PARAMETRE KALIBRASYONU
        frame1 = tk.Frame(self.parent, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        frame1.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame1, text="--- OCR PARAMETRE KALIBRASYONU ---", bg=self.card_bg, fg=self.gold, font=self.font_header).pack(pady=5)
        
        params = [
            ("PREPROCESS_PADDING", 0, 80, 30),
            ("TARGET_HEIGHT", 48, 256, 96),
            ("DARK_MODE_THRESHOLD", 50, 200, 127),
            ("MIN_CONTOUR_HEIGHT", 5, 50, 14),
            ("MIN_CONTOUR_WIDTH", 10, 100, 25),
            ("MORPH_KERNEL_W", 10, 100, 40),
            ("MORPH_KERNEL_H", 1, 20, 5)
        ]
        
        slider_frame = tk.Frame(frame1, bg=self.card_bg)
        slider_frame.pack(fill="x", padx=10, pady=5)
        
        for name, min_val, max_val, default in params:
            row = tk.Frame(slider_frame, bg=self.card_bg)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name, bg=self.card_bg, fg=self.fg, font=self.font_body, width=25, anchor="w").pack(side="left")
            
            val_var = tk.IntVar(value=getattr(OCREngine, name, default))
            slider = tk.Scale(row, from_=min_val, to=max_val, orient="horizontal", bg=self.card_bg, fg=self.fg, 
                              highlightthickness=0, troughcolor=self.bg, activebackground=self.accent, variable=val_var,
                              command=lambda v, n=name: self.update_ocr_param(n, v))
            slider.pack(side="left", fill="x", expand=True)
            self.sliders[name] = (slider, val_var, default)
            
        tk.Button(frame1, text="[ VARSAYILANLARA SIFIRLA ]", bg=self.bg, fg=self.gold, font=self.font_body,
                  command=self.reset_defaults, activebackground=self.accent).pack(pady=5)
                  
        # Section 2: IFADE BEYAZ LISTE EDITORU
        frame2 = tk.Frame(self.parent, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        frame2.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame2, text="--- IFADE BEYAZ LISTE EDITORU ---", bg=self.card_bg, fg=self.accent, font=self.font_header).pack(pady=5)
        
        self.words_text = tk.Text(frame2, bg=self.bg, fg=self.fg, font=self.font_body, height=4, width=50)
        self.words_text.pack(pady=5)
        self.update_words_display()
        
        word_ctrl = tk.Frame(frame2, bg=self.card_bg)
        word_ctrl.pack(pady=5)
        
        self.word_entry = tk.Entry(word_ctrl, bg=self.bg, fg=self.fg, font=self.font_body, insertbackground=self.fg)
        self.word_entry.pack(side="left", padx=5)
        
        tk.Button(word_ctrl, text="[ EKLE ]", bg=self.bg, fg=self.fg, font=self.font_body, command=self.add_word).pack(side="left", padx=2)
        tk.Button(word_ctrl, text="[ CIKAR ]", bg=self.bg, fg=self.error, font=self.font_body, command=self.remove_word).pack(side="left", padx=2)
        
        # Section 3: CANLI TEST
        frame3 = tk.Frame(self.parent, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        frame3.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame3, text="--- CANLI TEST ---", bg=self.card_bg, fg=self.gold, font=self.font_header).pack(pady=5)
        
        test_ctrl = tk.Frame(frame3, bg=self.card_bg)
        test_ctrl.pack(pady=5)
        
        self.test_entry = tk.Entry(test_ctrl, bg=self.bg, fg=self.fg, font=self.font_body, width=40, insertbackground=self.fg)
        self.test_entry.pack(side="left", padx=5)
        
        tk.Button(test_ctrl, text="[ TEST ET ]", bg=self.bg, fg=self.accent, font=self.font_body, command=self.run_test).pack(side="left", padx=5)
        
        self.test_result = tk.Label(frame3, text="", bg=self.card_bg, font=self.font_header)
        self.test_result.pack(pady=5)

    def update_ocr_param(self, name, value):
        setattr(OCREngine, name, int(value))

    def reset_defaults(self):
        for name, (slider, var, default) in self.sliders.items():
            var.set(default)
            self.update_ocr_param(name, default)

    def update_words_display(self):
        self.words_text.delete(1.0, tk.END)
        self.words_text.insert(tk.END, ", ".join(sorted(MathEngine.SAFE_WORDS)))

    def add_word(self):
        word = self.word_entry.get().strip()
        if word:
            MathEngine.SAFE_WORDS.add(word)
            self.update_words_display()
            self.word_entry.delete(0, tk.END)

    def remove_word(self):
        word = self.word_entry.get().strip()
        if word in MathEngine.SAFE_WORDS:
            MathEngine.SAFE_WORDS.remove(word)
            self.update_words_display()
            self.word_entry.delete(0, tk.END)

    def run_test(self):
        expr = self.test_entry.get()
        if not expr:
            return
            
        def test_task():
            try:
                formatted = MathEngine.format_input(expr)
                valid, msg = MathEngine._lexical_validation(formatted)
                self.admin.after(0, lambda: self.show_test_result(valid, msg))
            except Exception as e:
                self.admin.after(0, lambda: self.show_test_result(False, str(e)))
                
        threading.Thread(target=test_task, daemon=True).start()

    def show_test_result(self, valid, msg):
        if valid:
            self.test_result.config(text=f"PASS: {msg}", fg="#00FF41")
        else:
            self.test_result.config(text=f"FAIL: {msg}", fg=self.error)

