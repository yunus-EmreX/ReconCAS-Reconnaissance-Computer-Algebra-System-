import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageGrab, ImageEnhance
import pytesseract
import re
import ctypes
import threading
import time
import gc
import sqlite3
import hashlib
from datetime import datetime

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D 

# --- SİSTEM AYARLARI ---
plt.style.use('dark_background')
try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: pass

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

THEME = {
    "bg": "#050505", "fg": "#00FF41", "btn_bg": "#111111", 
    "active": "#008F11", "accent": "#00FFFF", "grid": "#333333",
    "font_main": ("Consolas", 10, "bold"), "font_title": ("Consolas", 11, "bold")
}

# ==========================================
# 1. MODÜL: DBEngine (Veritabanı & Geçmiş)
# ==========================================
class DBEngine:
    # Veritabanını her zaman Python dosyasının çalıştığı klasöre kurmasını garantileyen kod:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_NAME = os.path.join(BASE_DIR, "math_terminal_v8.db")
    
    @staticmethod
    def init_db():
        conn = sqlite3.connect(DBEngine.DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, hint TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS history 
                     (id INTEGER PRIMARY KEY, user_id INTEGER, equation TEXT, result TEXT, timestamp TEXT)''')
        conn.commit()
        conn.close()
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def register(username, password, hint):
        try:
            conn = sqlite3.connect(DBEngine.DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password_hash, hint) VALUES (?, ?, ?)", 
                      (username, DBEngine.hash_password(password), hint))
            conn.commit()
            conn.close()
            return True, "KAYIT BAŞARILI."
        except sqlite3.IntegrityError:
            return False, "BU KULLANICI ADI ZATEN MEVCUT."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def login(username, password):
        conn = sqlite3.connect(DBEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password_hash=?", 
                  (username, DBEngine.hash_password(password)))
        user = c.fetchone()
        conn.close()
        if user: return True, user[0]
        return False, "KİMLİK DOĞRULAMA BAŞARISIZ."

    @staticmethod
    def reset_password(username, hint, new_password):
        conn = sqlite3.connect(DBEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND hint=?", (username, hint))
        if c.fetchone():
            c.execute("UPDATE users SET password_hash=? WHERE username=?", 
                      (DBEngine.hash_password(new_password), username))
            conn.commit()
            conn.close()
            return True, "PAROLA GÜNCELLENDİ."
        conn.close()
        return False, "KULLANICI ADI VEYA GİZLİ YANIT HATALI."

    @staticmethod
    def add_history(user_id, equation, result):
        if not user_id: return
        conn = sqlite3.connect(DBEngine.DB_NAME)
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO history (user_id, equation, result, timestamp) VALUES (?, ?, ?, ?)", 
                  (user_id, equation, result, timestamp))
        conn.commit()
        conn.close()

    @staticmethod
    def get_history(user_id):
        conn = sqlite3.connect(DBEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT timestamp, equation, result FROM history WHERE user_id=? ORDER BY id DESC LIMIT 50", (user_id,))
        records = c.fetchall()
        conn.close()
        return records

# ==========================================
# 2. MODÜL: AuthGUI (Giriş Sistemi)
# ==========================================
class AuthGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SYSTEM.LOGIN // V8.0")
        self.geometry("380x420")
        self.resizable(False, False)
        self.configure(bg=THEME["bg"])
        DBEngine.init_db()
        self.current_user_id = None
        self.build_ui()
        
    def build_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        
        tk.Label(self, text="=== TERMINAL AUTH ===", font=("Consolas", 16, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self, text=">_ USERNAME:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.ent_user = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], relief="flat")
        self.ent_user.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ PASSWORD:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.ent_pass = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], relief="flat", show="*")
        self.ent_pass.pack(fill="x", padx=40, pady=5)
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1, "highlightthickness": 1, "highlightbackground": THEME["fg"]}
        
        tk.Button(self, text="[ LOGIN ]", command=self.do_login, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="[ CREATE_ACCOUNT ]", command=self.show_register, **btn_st).pack(fill="x", padx=40, pady=5)
        tk.Button(self, text="[ FORGOT_PASSWORD ]", command=self.show_reset, fg=THEME["accent"], bg=THEME["btn_bg"], font=THEME["font_main"], relief="flat", bd=0, activebackground=THEME["bg"]).pack(pady=10)

    def do_login(self):
        u, p = self.ent_user.get(), self.ent_pass.get()
        success, user_id_or_msg = DBEngine.login(u, p)
        if success:
            self.current_user_id = user_id_or_msg
            self.destroy() # Arayüzü kapat, ana terminali aç
        else:
            messagebox.showerror("AUTH_FAILED", user_id_or_msg)

    def show_register(self):
        for widget in self.winfo_children(): widget.destroy()
        tk.Label(self, text="=== NEW OPERATIVE ===", font=("Consolas", 16, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self, text=">_ SET USERNAME:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_user = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.reg_user.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ SET PASSWORD:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_pass = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], show="*")
        self.reg_pass.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ SECRET HINT (Forgot Pass):", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_hint = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.reg_hint.pack(fill="x", padx=40, pady=5)
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1, "highlightthickness": 1, "highlightbackground": THEME["fg"]}
        tk.Button(self, text="[ REGISTER_PROTOCOL ]", command=self.do_register, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="<< BACK", command=self.build_ui, bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack()

    def do_register(self):
        success, msg = DBEngine.register(self.reg_user.get(), self.reg_pass.get(), self.reg_hint.get())
        messagebox.showinfo("SYS_MSG", msg)
        if success: self.build_ui()

    def show_reset(self):
        for widget in self.winfo_children(): widget.destroy()
        tk.Label(self, text="=== PASSWORD OVERRIDE ===", font=("Consolas", 16, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self, text=">_ USERNAME:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.res_user = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.res_user.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ SECRET HINT:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.res_hint = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.res_hint.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ NEW PASSWORD:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.res_pass = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], show="*")
        self.res_pass.pack(fill="x", padx=40, pady=5)
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1, "highlightthickness": 1, "highlightbackground": THEME["fg"]}
        tk.Button(self, text="[ INITIATE_OVERRIDE ]", command=self.do_reset, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="<< BACK", command=self.build_ui, bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack()

    def do_reset(self):
        success, msg = DBEngine.reset_password(self.res_user.get(), self.res_hint.get(), self.res_pass.get())
        messagebox.showinfo("SYS_MSG", msg)
        if success: self.build_ui()

# ==========================================
# 3. MODÜL: OCREngine & MathEngine
# ==========================================
class OCREngine:
    @staticmethod
    def enhance_image(img, is_full_screen=False):
        width, height = img.size
        scale = 1.2 if is_full_screen else 2.0
        resample_mode = Image.Resampling.BILINEAR if is_full_screen else Image.Resampling.BICUBIC
        img = img.resize((int(width * scale), int(height * scale)), resample_mode).convert('L')
        if not is_full_screen: img = ImageEnhance.Sharpness(img).enhance(2.0)
        return ImageEnhance.Contrast(img).enhance(1.5)

    @staticmethod
    def extract_equations(bbox, is_full_screen=False):
        img = ImageGrab.grab(bbox=bbox)
        enhanced_img = OCREngine.enhance_image(img, is_full_screen)
        psm = '--psm 3' if is_full_screen else '--psm 6'
        text = pytesseract.image_to_string(enhanced_img, config=psm).strip()
        img.close(); enhanced_img.close()
        
        if not text: return []
        text = re.sub(r'[—–_~−]', '-', text).replace('×', '*').replace('÷', '/').replace(':', '/')
        equations, current_expr = [], ""
        for line in text.split('\n'):
            line = line.strip()
            if not line or re.match(r'^[\-=]{2,}$', line.replace(' ', '')): continue
            if re.match(r'^[+\-\*/]', line) and current_expr: current_expr += " " + line
            else:
                if current_expr: equations.append(current_expr)
                current_expr = line
        if current_expr: equations.append(current_expr)
        return equations

class MathEngine:
    TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
    @staticmethod
    def format_input(text): return text.replace('^', '**').replace(',', '.').replace('[', '(').replace(']', ')')

    @staticmethod
    def is_advanced(text):
        if any(op in text for op in ['=', '>', '<']): return True
        try:
            parsed = parse_expr(MathEngine.format_input(text), transformations=MathEngine.TRANSFORMATIONS)
            return len(parsed.free_symbols) > 0
        except: return False

    @staticmethod
    def evaluate_basic(text):
        try:
            expr_str = MathEngine.format_input(text).replace('x', '*').replace('X', '*').replace('√', 'sqrt')
            expr_str = re.sub(r'(\d+)!', r'factorial(\1)', expr_str)
            parsed = parse_expr(expr_str, transformations=MathEngine.TRANSFORMATIONS)
            result = parsed.evalf()
            return int(result) if result.is_integer else round(float(result), 4)
        except: return None

    @staticmethod
    def analyze_advanced(text):
        expr_str = MathEngine.format_input(text)
        try:
            if '=' in expr_str:
                parts = expr_str.split('=', 1)
                left = parse_expr(parts[0], transformations=MathEngine.TRANSFORMATIONS)
                right = parse_expr(parts[1], transformations=MathEngine.TRANSFORMATIONS)
                return True, left - right, sp.solve(sp.Eq(left, right))
            else:
                return False, sp.simplify(parse_expr(expr_str, transformations=MathEngine.TRANSFORMATIONS)), None
        except Exception as e: raise Exception(f"Sözdizimi Hatası: {str(e)}")

# ==========================================
# 4. MODÜL: TerminalGUI (Ana Menü)
# ==========================================
class TerminalGUI(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.title("SYSTEM.CORE // V8.0 ENTERPRISE")
        self.geometry("380x300")
        self.resizable(False, False)
        self.attributes('-topmost', True) 
        self.configure(bg=THEME["bg"])
        self.is_live = False
        self.setup_main_menu()

    def setup_main_menu(self):
        header = tk.Frame(self, bg=THEME["bg"])
        header.pack(fill="x", pady=5)
        tk.Label(header, text=">_ AUTHORIZATION: ACCEPTED", font=("Consolas", 9), fg=THEME["accent"], bg=THEME["bg"]).pack()
        tk.Label(header, text="OPERASYON PROTOKOLÜ SEÇİNİZ:", font=THEME["font_title"], fg=THEME["fg"], bg=THEME["bg"]).pack(pady=5)
        
        btn_style = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], 
                     "relief": "flat", "bd": 1, "highlightthickness": 1, "highlightbackground": THEME["fg"], "cursor": "tcross"}

        tk.Button(self, text="[ ALAN_SEÇ_VE_ANALİZ_ET ]", command=lambda: self.prepare_snipping("single"), **btn_style).pack(pady=3, padx=20, fill="x")
        self.btn_live_area = tk.Button(self, text="[ CANLI_BÖLGE_İZLEMESİ ]", command=self.toggle_live_area, **btn_style)
        self.btn_live_area.pack(pady=3, padx=20, fill="x")
        
        # YENİ BUTONLAR
        tk.Button(self, text="[ SANDBOX_SIM_STUDIO ]", command=self.open_sandbox, font=THEME["font_main"], bg="#4A148C", fg="white", relief="flat", bd=1, highlightthickness=1, highlightbackground=THEME["accent"]).pack(pady=8, padx=20, fill="x")
        tk.Button(self, text="[ İŞLEM_GEÇMİŞİ_LOGLARI ]", command=self.open_history, font=("Consolas", 9), bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack(pady=2, fill="x")

    def open_history(self):
        hist = tk.Toplevel(self)
        hist.title("DATA_LOGS")
        hist.geometry("500x400")
        hist.configure(bg=THEME["bg"])
        hist.attributes('-topmost', True)
        
        txt = tk.Text(hist, font=("Consolas", 9), bg=THEME["btn_bg"], fg=THEME["fg"], relief="flat")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        
        records = DBEngine.get_history(self.user_id)
        if not records: txt.insert(tk.END, ">_ GEÇMİŞ LOG BULUNAMADI.")
        else:
            for r in records:
                txt.insert(tk.END, f"[{r[0]}]\nGİRDİ: {r[1]}\nÇIKTI: {r[2]}\n{'-'*40}\n")
        txt.config(state="disabled")

    def toggle_live_area(self):
        if not self.is_live: self.prepare_snipping("live_area")
        else: self.stop_live_mode()

    def prepare_snipping(self, mode):
        self.current_mode = mode
        self.withdraw() 
        self.after(200, self.show_overlay)

    def show_overlay(self):
        self.overlay = tk.Toplevel(self)
        self.overlay.attributes('-fullscreen', True, '-alpha', 0.3, '-topmost', True)
        self.overlay.config(cursor="tcross")
        self.canvas = tk.Canvas(self.overlay, cursor="tcross", bg="black")
        self.canvas.pack(fill="both", expand=True)
        self.start_x, self.start_y, self.rect = None, None, None
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.overlay.bind("<Escape>", lambda e: self.cancel_snipping())

    def on_button_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        color = THEME["accent"] if self.current_mode == "single" else THEME["fg"]
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline=color, width=2, fill="gray", stipple="gray12")

    def on_move_press(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        self.overlay.destroy() 
        if x2 - x1 > 10 and y2 - y1 > 10:
            if self.current_mode == "single": self.process_single((x1, y1, x2, y2))
            else: self.start_live_mode((x1, y1, x2, y2), mode="live_area")
        else: self.deiconify()

    def cancel_snipping(self):
        self.overlay.destroy(); self.deiconify()

    def show_popup(self, title, message):
        pop = tk.Toplevel(self)
        pop.title(title); pop.geometry("450x150")
        pop.configure(bg=THEME["bg"]); pop.attributes('-topmost', True)
        tk.Label(pop, text=message, font=("Consolas", 10), fg=THEME["fg"], bg=THEME["bg"], justify="left").pack(expand=True, padx=10, pady=10)
        tk.Button(pop, text="[ KAPAT ]", font=THEME["font_main"], bg=THEME["btn_bg"], fg=THEME["accent"], relief="flat", command=pop.destroy).pack(pady=10)

    def process_single(self, bbox):
        try:
            equations = OCREngine.extract_equations(bbox)
            if not equations:
                self.show_popup("SYSTEM_WARNING", "OKUNABİLİR VERİ TESPİT EDİLEMEDİ.")
                self.deiconify()
                return
            first_eq = equations[0]
            if MathEngine.is_advanced(first_eq):
                self.open_lab_window(first_eq)
            else:
                res = MathEngine.evaluate_basic(first_eq)
                if res is not None:
                    DBEngine.add_history(self.user_id, first_eq, str(res)) # GEÇMİŞE KAYDET
                    self.show_popup("HESAP_SONUCU", f"> GİRDİ: {first_eq}\n> ÇIKTI: {res}")
                else: self.show_popup("SYSTEM_ERROR", f"ÇÖZÜMLENEMEYEN SÖZDİZİMİ:\n{first_eq}")
                self.deiconify()
        except Exception as e:
            self.show_popup("FATAL_ERROR", f"SİSTEM HATASI:\n{e}")
            self.deiconify()

    def start_live_mode(self, bbox, mode):
        self.is_live = True
        self.btn_live_area.config(state="disabled", text="[ İZLEMEYİ_DURDUR ]", fg=THEME["accent"])
        self.btn_single.config(state="disabled")
        self.deiconify()

        self.live_window = tk.Toplevel(self)
        self.live_window.title("LIVE_STREAM")
        self.live_window.geometry("300x200+20+20") 
        self.live_window.attributes('-topmost', True, '-alpha', 0.9)
        self.live_window.config(bg=THEME["bg"])
        self.live_text_var = tk.StringVar(value=">_ BÖLGE_İZLENİYOR...")
        tk.Label(self.live_window, textvariable=self.live_text_var, font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"], justify="left", anchor="nw").pack(fill="both", expand=True, padx=10, pady=10)

        threading.Thread(target=self.live_loop, args=(bbox, mode), daemon=True).start()

    def stop_live_mode(self):
        self.is_live = False
        if hasattr(self, 'live_window') and self.live_window: self.live_window.destroy()
        self.btn_live_area.config(text="[ CANLI_BÖLGE_İZLEMESİ ]", fg=THEME["fg"], state="normal")
        self.btn_single.config(state="normal")

    def live_loop(self, bbox, mode):
        while self.is_live:
            try:
                equations = OCREngine.extract_equations(bbox, is_full_screen=False)
                results = []
                for i, eq in enumerate(equations, 1):
                    if not OCREngine.is_actual_math(eq): continue
                    if MathEngine.is_advanced(eq):
                        try:
                            _, parsed, _ = MathEngine.analyze_advanced(eq)
                            results.append(f"[{i}] {eq} => {parsed}")
                        except: pass
                    else:
                        res = MathEngine.evaluate_basic(eq)
                        if res is not None: results.append(f"[{i}] {eq} = {res}")
                if results: self.after(0, lambda t=">_ VERİ_AKISI:\n" + "\n".join(results): self.live_text_var.set(t))
                else: self.after(0, lambda: self.live_text_var.set(">_ İŞLEM_BEKLENİYOR..."))
            except: pass
            time.sleep(1.0)

    # --- 5. CAS LABORATUVARI (V7'DEN ALINDI) ---
    def open_lab_window(self, original_text):
        self.lab = tk.Toplevel(self)
        self.lab.title("CAS_LAB // STANDARD_ANALYSIS")
        self.lab.geometry("850x700")
        self.lab.configure(bg=THEME["bg"])
        self.lab.attributes('-topmost', True) 
        self.current_canvas = None 
        self.current_sympy_expr = None

        edit_frame = tk.Frame(self.lab, bg=THEME["btn_bg"], bd=1, highlightbackground=THEME["fg"], highlightthickness=1)
        edit_frame.pack(fill="x", padx=10, pady=10)
        self.entry_expr = tk.Entry(edit_frame, font=("Consolas", 14), width=40, bg=THEME["bg"], fg=THEME["accent"], insertbackground=THEME["fg"], relief="flat")
        self.entry_expr.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        self.entry_expr.insert(0, original_text)
        tk.Button(edit_frame, text="[ İŞLE ]", font=THEME["font_main"], bg=THEME["bg"], fg=THEME["fg"], relief="flat", command=self.update_lab).pack(side="right", padx=10, pady=5)

        self.graph_frame = tk.Frame(self.lab, bg=THEME["bg"], bd=1, highlightbackground=THEME["accent"], highlightthickness=1)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=5)

        console_frame = tk.Frame(self.lab, bg=THEME["bg"])
        console_frame.pack(fill="x", padx=10, pady=5)
        self.console = tk.Text(console_frame, height=4, bg=THEME["bg"], fg=THEME["fg"], font=("Consolas", 10), relief="flat")
        self.console.pack(fill="both", expand=True)
        
        self.lab.protocol("WM_DELETE_WINDOW", self.on_lab_close)
        self.update_lab()

    def update_lab(self):
        raw_text = self.entry_expr.get().strip()
        try:
            is_eq, expr, roots = MathEngine.analyze_advanced(raw_text)
            self.current_sympy_expr = expr
            log_str = f"DENKLEM_ONAYLANDI\nSTANDART_FORM: {expr}=0\nÇÖZÜM: {roots}" if is_eq else f"İFADE_ONAYLANDI\nSADE_FORM: {expr}"
            
            DBEngine.add_history(self.user_id, raw_text, str(roots if is_eq else expr))
            
            self.console.config(state="normal")
            self.console.delete("1.0", tk.END); self.console.insert(tk.END, ">_ " + log_str)
            self.console.config(state="disabled")
            
            self.clear_graph()
            self.draw_graph(expr, self.graph_frame)
        except Exception as e:
            self.console.config(state="normal"); self.console.delete("1.0", tk.END); self.console.insert(tk.END, f">_ SİSTEM_HATASI: {e}"); self.console.config(state="disabled")
            self.clear_graph()

    def clear_graph(self):
        if self.current_canvas:
            self.current_canvas.get_tk_widget().destroy()
            plt.clf(); plt.close('all'); gc.collect()
            self.current_canvas = None

    def draw_graph(self, sympy_expr, parent_frame):
        if sympy_expr is None: return
        symbols = sorted(list(sympy_expr.free_symbols), key=lambda s: s.name)
        if len(symbols) == 1:
            x_sym = symbols[0]
            f_lambdified = sp.lambdify(x_sym, sympy_expr, modules=['numpy'])
            x_vals = np.linspace(-10, 10, 400)
            try:
                y_vals = f_lambdified(x_vals)
                if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
                fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
                fig.patch.set_facecolor(THEME["bg"]); ax.set_facecolor(THEME["bg"])
                ax.plot(x_vals, y_vals, color=THEME["fg"], linewidth=2)
                ax.axhline(0, color=THEME["accent"], linewidth=1); ax.axvline(0, color=THEME["accent"], linewidth=1)
                ax.grid(color=THEME["grid"], linestyle=':', linewidth=1)
                for spine in ax.spines.values(): spine.set_color(THEME["fg"])
                ax.tick_params(colors=THEME["fg"])
                self.current_canvas = FigureCanvasTkAgg(fig, master=parent_frame)
                self.current_canvas.draw(); self.current_canvas.get_tk_widget().pack(fill="both", expand=True)
            except: pass
        elif len(symbols) == 2:
            x_sym, y_sym = symbols[0], symbols[1]
            f_lambdified = sp.lambdify((x_sym, y_sym), sympy_expr, modules=['numpy'])
            X, Y = np.meshgrid(np.linspace(-10, 10, 50), np.linspace(-10, 10, 50))
            try:
                Z = f_lambdified(X, Y)
                if isinstance(Z, (int, float)): Z = np.full_like(X, Z)
                fig = plt.figure(figsize=(6, 4), dpi=100)
                fig.patch.set_facecolor(THEME["bg"])
                ax = fig.add_subplot(111, projection='3d')
                ax.set_facecolor(THEME["bg"])
                ax.plot_surface(X, Y, Z, cmap='cool', alpha=0.9, edgecolor='none')
                ax.tick_params(colors=THEME["accent"])
                self.current_canvas = FigureCanvasTkAgg(fig, master=parent_frame)
                self.current_canvas.draw(); self.current_canvas.get_tk_widget().pack(fill="both", expand=True)
            except: pass

    def on_lab_close(self):
        self.clear_graph(); self.lab.destroy(); self.deiconify()

    # --- 6. SANDBOX SIM STUDIO (KENDİ UZAYIN) ---
    def open_sandbox(self):
        self.withdraw()
        self.sandbox = tk.Toplevel(self)
        self.sandbox.title("SANDBOX_SIM_STUDIO // CUSTOM_UNIVERSE")
        self.sandbox.geometry("900x800")
        self.sandbox.configure(bg=THEME["bg"])
        self.sandbox.attributes('-topmost', True) 
        
        self.sb_canvas = None

        # KONTROL PANELİ
        ctrl_frame = tk.Frame(self.sandbox, bg=THEME["btn_bg"], bd=1, highlightbackground=THEME["accent"], highlightthickness=1)
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(ctrl_frame, text=">_ BAZ FONKSİYON f(x,y):", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["btn_bg"]).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_base = tk.Entry(ctrl_frame, font=("Consolas", 12), width=35, bg=THEME["bg"], fg=THEME["accent"], relief="flat")
        self.ent_base.grid(row=0, column=1, padx=5, pady=5)
        self.ent_base.insert(0, "sin(x) * cos(y)")

        tk.Label(ctrl_frame, text=">_ UZAY BÜKÜCÜ ÇARPAN U(x,y):", font=THEME["font_main"], fg="#E91E63", bg=THEME["btn_bg"]).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ent_warp = tk.Entry(ctrl_frame, font=("Consolas", 12), width=35, bg=THEME["bg"], fg="#E91E63", relief="flat")
        self.ent_warp.grid(row=1, column=1, padx=5, pady=5)
        self.ent_warp.insert(0, "x^2")

        tk.Button(ctrl_frame, text="[ EVRENİ SİMÜLE ET ]", font=THEME["font_main"], bg=THEME["bg"], fg=THEME["fg"], command=self.run_sandbox).grid(row=0, column=2, rowspan=2, padx=20, pady=5, sticky="nsew")

        # GRAFİK ALANI
        self.sb_graph_frame = tk.Frame(self.sandbox, bg="black", bd=1, highlightbackground=THEME["fg"], highlightthickness=1)
        self.sb_graph_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # DİRENÇ NOKTALARI (KRİTİK ANALİZ) TERMİNALİ
        self.sb_console = tk.Text(self.sandbox, height=6, bg=THEME["bg"], fg=THEME["accent"], font=("Consolas", 10), relief="flat")
        self.sb_console.pack(fill="x", padx=10, pady=10)
        
        self.sandbox.protocol("WM_DELETE_WINDOW", self.close_sandbox)
        self.run_sandbox()

    def run_sandbox(self):
        base_str = MathEngine.format_input(self.ent_base.get().strip())
        warp_str = MathEngine.format_input(self.ent_warp.get().strip())
        
        try:
            # İki formülü çarpıp "Yeni Evren" formülünü yaratıyoruz Z = f(x,y) * U(x,y)
            base_expr = parse_expr(base_str, transformations=MathEngine.TRANSFORMATIONS)
            warp_expr = parse_expr(warp_str, transformations=MathEngine.TRANSFORMATIONS)
            custom_universe_expr = sp.simplify(base_expr * warp_expr)
            
            self.sb_console.config(state="normal")
            self.sb_console.delete("1.0", tk.END)
            self.sb_console.insert(tk.END, f">_ YENİ EVREN KURULDU: {custom_universe_expr}\n")
            
            # Grafiği Çiz ve Direnç Noktalarını Hesapla
            if self.sb_canvas:
                self.sb_canvas.get_tk_widget().destroy()
                plt.clf(); plt.close('all'); gc.collect()
                self.sb_canvas = None

            symbols = sorted(list(custom_universe_expr.free_symbols), key=lambda s: s.name)
            
            # --- 2D SANDBOX ---
            if len(symbols) == 1:
                x_sym = symbols[0]
                f_lambdified = sp.lambdify(x_sym, custom_universe_expr, modules=['numpy'])
                x_vals = np.linspace(-10, 10, 400)
                
                # SIFIRA BÖLME VEYA LOG(-1) GİBİ SİMÜLASYON ÇÖKMELERİNİ ENGELLE
                with np.errstate(all='ignore'):
                    y_vals = f_lambdified(x_vals)
                
                # DİRENÇ NOKTALARI ANALİZİ (Maksimum/Minimum Zirveler)
                valid_y = y_vals[np.isfinite(y_vals)] # Sonsuzlukları yoksay
                if len(valid_y) > 0:
                    max_res = np.max(valid_y)
                    min_res = np.min(valid_y)
                    self.sb_console.insert(tk.END, f">_ DİRENÇ TAVANI (MAX): {max_res:.2f}\n>_ DİRENÇ TABANI (MIN): {min_res:.2f}\n")
                
                fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
                fig.patch.set_facecolor(THEME["bg"]); ax.set_facecolor(THEME["bg"])
                ax.plot(x_vals, y_vals, color="#E91E63", linewidth=2)
                ax.axhline(0, color=THEME["fg"], linewidth=1); ax.axvline(0, color=THEME["fg"], linewidth=1)
                ax.grid(color=THEME["grid"], linestyle=':', linewidth=1)
                for spine in ax.spines.values(): spine.set_color(THEME["fg"])
                ax.tick_params(colors=THEME["fg"])

                self.sb_canvas = FigureCanvasTkAgg(fig, master=self.sb_graph_frame)
                self.sb_canvas.draw(); self.sb_canvas.get_tk_widget().pack(fill="both", expand=True)

            # --- 3D SANDBOX ---
            elif len(symbols) == 2:
                x_sym, y_sym = symbols[0], symbols[1]
                f_lambdified = sp.lambdify((x_sym, y_sym), custom_universe_expr, modules=['numpy'])
                X, Y = np.meshgrid(np.linspace(-10, 10, 50), np.linspace(-10, 10, 50))
                
                with np.errstate(all='ignore'):
                    Z = f_lambdified(X, Y)
                    
                valid_z = Z[np.isfinite(Z)]
                if len(valid_z) > 0:
                    self.sb_console.insert(tk.END, f">_ KRİTİK ZİRVE (MAX Z): {np.max(valid_z):.2f}\n>_ KRİTİK ÇUKUR (MIN Z): {np.min(valid_z):.2f}\n")

                fig = plt.figure(figsize=(6, 4), dpi=100)
                fig.patch.set_facecolor(THEME["bg"])
                ax = fig.add_subplot(111, projection='3d')
                ax.set_facecolor(THEME["bg"])
                
                # Siberpunk 3D Modeli
                ax.plot_surface(X, Y, Z, cmap='magma', alpha=0.9, edgecolor='none')
                ax.tick_params(colors=THEME["accent"])

                self.sb_canvas = FigureCanvasTkAgg(fig, master=self.sb_graph_frame)
                self.sb_canvas.draw(); self.sb_canvas.get_tk_widget().pack(fill="both", expand=True)

            else:
                self.sb_console.insert(tk.END, ">_ HATA: LÜTFEN SADECE 'x' VEYA 'x, y' DEĞİŞKENLERİ KULLANIN.\n")
                
            self.sb_console.config(state="disabled")

        except Exception as e:
            self.sb_console.config(state="normal")
            self.sb_console.delete("1.0", tk.END)
            self.sb_console.insert(tk.END, f">_ EVREN ÇÖKÜŞÜ (HATA): {e}\nLütfen geçerli bir matematiksel kural girin.")
            self.sb_console.config(state="disabled")

    def close_sandbox(self):
        if self.sb_canvas:
            self.sb_canvas.get_tk_widget().destroy()
            plt.clf(); plt.close('all'); gc.collect()
            self.sb_canvas = None
        self.sandbox.destroy()
        self.deiconify()

# ==========================================
# BOOT SİSTEMİ
# ==========================================
if __name__ == '__main__':
    try:
        auth_app = AuthGUI()
        auth_app.mainloop()
        
        if hasattr(auth_app, 'current_user_id') and auth_app.current_user_id:
            app = TerminalGUI(user_id=auth_app.current_user_id)
            app.mainloop()
    except Exception as e:
        import traceback
        print("\n" + "="*50)
        print("SİSTEM ÇÖKÜŞÜ - HATA RAPORU:")
        print("="*50)
        traceback.print_exc()
        print("="*50)
        input("\nHatayı okuduktan sonra çıkmak için ENTER tuşuna basın...")