import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import time
import gc
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import numpy as np
import sympy as sp

# Çekirdek modüller (Core & Vision)
from core.auth_engine import DatabaseEngine, AuthError
from core.math_engine import MathEngine, MathError, UnsafeExpressionException
from vision.ocr_engine import OCREngine, OCRError
from core.document_engine import DocumentEngine, DocumentError

# Siberpunk & Endüstriyel Tema Entegrasyonu
THEME = {
    "bg": "#050505", "fg": "#00FF41", "btn_bg": "#111111", 
    "active": "#008F11", "accent": "#00FFFF", "grid": "#333333",
    "font_main": ("Consolas", 10, "bold"), "font_title": ("Consolas", 11, "bold"),
    "error": "#FF003C", "warning": "#FFB300"
}

# ==========================================
# 1. KİMLİK DOĞRULAMA VE GÜVENLİK (AUTH GUI)
# ==========================================
class AuthGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SYSTEM.LOGIN // V0.1 PRE-RELEASE")
        self.geometry("380x440")
        self.resizable(False, False)
        self.configure(bg=THEME["bg"])
        self.current_user_id = None
        
        try:
            DatabaseEngine.init_db()
        except AuthError as e:
            messagebox.showerror("CRITICAL_DB_ERROR", str(e))
            self.destroy()
            
        self.build_ui()
        
    def build_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        tk.Label(self, text="=== TERMINAL AUTH ===", font=("Consolas", 16, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self, text=">_ USERNAME:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.ent_user = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.ent_user.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ PASSWORD:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.ent_pass = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], show="*")
        self.ent_pass.pack(fill="x", padx=40, pady=5)
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1}
        tk.Button(self, text="[ LOGIN ]", command=self.do_login, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="[ CREATE_ACCOUNT ]", command=self.show_register, **btn_st).pack(fill="x", padx=40, pady=5)
        tk.Button(self, text="[ FORGOT_PASSWORD ]", command=self.show_reset, fg=THEME["accent"], bg=THEME["btn_bg"], font=THEME["font_main"], relief="flat", bd=0).pack(pady=10)

    def do_login(self):
        username = self.ent_user.get()
        success, res = DatabaseEngine.login(username, self.ent_pass.get())
        if success:
            self.current_user_id = res
            DatabaseEngine.log_session_activity(self.current_user_id, "SYSTEM_AUTH", "LOGIN_SUCCESS")
            self.destroy()
        else: 
            messagebox.showerror("AUTH_FAILED", res)

    def show_register(self):
        for widget in self.winfo_children(): widget.destroy()
        tk.Label(self, text="=== NEW OPERATIVE ===", font=("Consolas", 16, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self, text=">_ SET USERNAME:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_user = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.reg_user.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ SET PASSWORD:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_pass = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], show="*")
        self.reg_pass.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ SECRET HINT (For Reset):", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_hint = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.reg_hint.pack(fill="x", padx=40, pady=5)
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1}
        tk.Button(self, text="[ REGISTER_PROTOCOL ]", command=self.do_register, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="<< BACK", command=self.build_ui, bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack()

    def do_register(self):
        try:
            success, msg = DatabaseEngine.register(self.reg_user.get(), self.reg_pass.get(), self.reg_hint.get())
            messagebox.showinfo("SYS_MSG", msg)
            if success: self.build_ui()
        except AuthError as e: messagebox.showerror("AUTH_ERROR", str(e))

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
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1}
        tk.Button(self, text="[ OVERRIDE_PROTOCOL ]", command=self.do_reset, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="<< BACK", command=self.build_ui, bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack()

    def do_reset(self):
        success, msg = DatabaseEngine.reset_password(self.res_user.get(), self.res_hint.get(), self.res_pass.get())
        if success:
            messagebox.showinfo("SYS_MSG", msg)
            self.build_ui()
        else:
            messagebox.showerror("AUTH_ERROR", msg)


# ==========================================
# 2. ANA TERMİNAL (VISION VE OCR MERKEZİ)
# ==========================================
class AnimatedToggle(tk.Canvas):
    """Sağa kayarak açılan Siberpunk Toggle Butonu"""
    def __init__(self, parent, command=None):
        super().__init__(parent, width=50, height=24, bg=THEME["bg"], highlightthickness=0)
        self.state = False
        self.command = command
        
        # Arka plan hapı
        self.bg_id = self.create_oval(2, 2, 22, 22, fill=THEME["btn_bg"], outline=THEME["grid"])
        self.bg_id2 = self.create_oval(28, 2, 48, 22, fill=THEME["btn_bg"], outline=THEME["grid"])
        self.bg_rect = self.create_rectangle(12, 2, 38, 22, fill=THEME["btn_bg"], outline=THEME["btn_bg"])
        
        # Hareketli daire (Switch)
        self.circle_id = self.create_oval(4, 4, 20, 20, fill="#555555", outline="#555555")
        self.bind("<Button-1>", self.toggle)
        
    def toggle(self, event=None):
        self.state = not self.state
        if self.state:
            self.itemconfig(self.bg_id, fill=THEME["active"], outline=THEME["active"])
            self.itemconfig(self.bg_id2, fill=THEME["active"], outline=THEME["active"])
            self.itemconfig(self.bg_rect, fill=THEME["active"], outline=THEME["active"])
            self.itemconfig(self.circle_id, fill="#000000")
            self.coords(self.circle_id, 30, 4, 46, 20) 
        else:
            self.itemconfig(self.bg_id, fill=THEME["btn_bg"], outline=THEME["grid"])
            self.itemconfig(self.bg_id2, fill=THEME["btn_bg"], outline=THEME["grid"])
            self.itemconfig(self.bg_rect, fill=THEME["btn_bg"], outline=THEME["btn_bg"])
            self.itemconfig(self.circle_id, fill="#555555")
            self.coords(self.circle_id, 4, 4, 20, 20) 
            
        if self.command:
            self.command(self.state)

class TerminalGUI(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.title("SYSTEM.CORE // V0.1 ENTERPRISE")
        self.geometry("400x420")
        self.resizable(False, False)
        self.attributes('-topmost', True) 
        self.configure(bg=THEME["bg"])
        self.is_live = False
        self.debug_mode = False 
        self.ocr = OCREngine()
        self.setup_main_menu()

    def set_debug(self, state):
        self.debug_mode = state

    def setup_main_menu(self):
        header = tk.Frame(self, bg=THEME["bg"])
        header.pack(fill="x", pady=5)
        tk.Label(header, text=">_ AUTH: ACCEPTED | SECURE_PARSER: ACTIVE", font=("Consolas", 9), fg=THEME["accent"], bg=THEME["bg"]).pack()
        
        # DEBUG TOGGLE PANELİ
        debug_frame = tk.Frame(self, bg=THEME["bg"])
        debug_frame.pack(fill="x", pady=5)
        tk.Label(debug_frame, text="[ OCR_DEBUG_MODU ]", font=("Consolas", 9, "bold"), fg=THEME["warning"], bg=THEME["bg"]).pack(side="left", padx=20)
        
        self.toggle_btn = AnimatedToggle(debug_frame, command=self.set_debug)
        self.toggle_btn.pack(side="right", padx=20)

        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1}

        self.btn_single = tk.Button(self, text="[ ALAN_SEÇ_VE_ANALİZ_ET ]", command=lambda: self.prepare_snipping("single"), **btn_st)
        self.btn_single.pack(pady=5, padx=20, fill="x")
        
        self.btn_live_area = tk.Button(self, text="[ CANLI_BÖLGE_İZLEMESİ ]", command=lambda: self.toggle_live("live_area"), **btn_st)
        self.btn_live_area.pack(pady=5, padx=20, fill="x")

        tk.Button(self, text="[ SANDBOX_SIM_STUDIO ]", command=self.open_sandbox, font=THEME["font_main"], bg="#4A148C", fg="white", relief="flat", bd=1).pack(pady=10, padx=20, fill="x")
        
        tk.Button(self, text="[ DOSYA_ANALİZİ (PNG/JPG/PDF) ]",
                  command=self.open_document_analyzer,
                  font=THEME["font_main"], bg="#00695C", fg="white",
                  relief="flat", bd=1).pack(pady=5, padx=20, fill="x")
        
        tk.Button(self, text="[ İŞLEM_GEÇMİŞİ_LOGLARI ]", command=self.open_history, font=("Consolas", 9), bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack(fill="x", pady=5)

    def open_document_analyzer(self):
        DocumentWindow(self, self.user_id)

    def toggle_live(self, mode):
        if not self.is_live: self.prepare_snipping(mode)
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
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline=THEME["accent"], width=2)

    def on_move_press(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        self.overlay.destroy() 
        if x2 - x1 > 10 and y2 - y1 > 10:
            if self.current_mode == "single": self.process_single((x1, y1, x2, y2))
            else: self.start_live_mode((x1, y1, x2, y2))
        else: self.deiconify()

    def cancel_snipping(self):
        self.overlay.destroy(); self.deiconify()

    def process_single(self, bbox):
        self.deiconify()
        first_eq = None  # Scope hatasını önlemek için önceden tanımla
        try:
            equations = self.ocr.extract_equations(bbox, debug=self.debug_mode)
            
            if not equations:
                msg = "VERİ BULUNAMADI.\n\nEğer OCR_DEBUG_MODU açıksa, ReconCAS ana klasöründeki 'logs' dizinine giderek Tesseract'ın tam olarak ne gördüğünü inceleyebilirsiniz."
                return messagebox.showwarning("SYS", msg)
            
            first_eq = equations[0]
            if MathEngine.is_advanced(first_eq):
                LabWindow(self, first_eq, self.user_id)
            else:
                res = MathEngine.evaluate_basic(first_eq)
                DatabaseEngine.log_session_activity(self.user_id, first_eq, str(res))
                messagebox.showinfo("RESULT", f"GİRDİ: {first_eq}\nÇIKTI: {res}")
        except UnsafeExpressionException as e:
            eq_label = first_eq if first_eq is not None else "<tanımsız>"
            DatabaseEngine.log_session_activity(self.user_id, eq_label, "SECURITY_BLOCK")
            messagebox.showerror("SECURITY_BLOCK", str(e))
        except Exception as e: messagebox.showerror("ERROR", str(e))

    def start_live_mode(self, bbox):
        self.is_live = True
        self.btn_live_area.config(state="normal", text="[ İZLEMEYİ_DURDUR ]", fg=THEME["accent"])
        self.btn_single.config(state="disabled")
        self.deiconify()

        self.live_window = tk.Toplevel(self)
        self.live_window.geometry("350x200+20+20") 
        self.live_window.attributes('-topmost', True, '-alpha', 0.9)
        self.live_window.config(bg=THEME["bg"])
        self.live_text_var = tk.StringVar(value=">_ BÖLGE_İZLENİYOR...")
        tk.Label(self.live_window, textvariable=self.live_text_var, font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"], justify="left").pack(fill="both", expand=True, padx=10, pady=10)

        threading.Thread(target=self.live_loop, args=(bbox,), daemon=True).start()

    def stop_live_mode(self):
        self.is_live = False
        if hasattr(self, 'live_window') and self.live_window: self.live_window.destroy()
        self.btn_live_area.config(text="[ CANLI_BÖLGE_İZLEMESİ ]", fg=THEME["fg"])
        self.btn_single.config(state="normal")

    def live_loop(self, bbox):
        while self.is_live:
            try:
                equations = self.ocr.extract_equations(bbox, use_frame_diff=True, debug=self.debug_mode)
                if equations is None: 
                    time.sleep(0.5)
                    continue
                
                results = []
                for eq in equations:
                    if not OCREngine.is_actual_math(eq): continue
                    try:
                        if MathEngine.is_advanced(eq):
                            _, parsed, _ = MathEngine.analyze_advanced(eq)
                            results.append(f"{eq} => {parsed}")
                        else:
                            res = MathEngine.evaluate_basic(eq)
                            results.append(f"{eq} = {res}")
                    except UnsafeExpressionException: results.append(f"[BLOCKED] {eq}")
                    except: pass
                
                if results:
                    # Thread-safe UI güncellemesi: closure yerine değeri kopyalayarak iç fonksiyon kullan
                    display_text = ">_ VERİ_AKISI:\n" + "\n".join(results)
                    def _update_ui(text=display_text):
                        self.live_text_var.set(text)
                    self.after(0, _update_ui)
            except: pass
            time.sleep(1.0)

    def open_sandbox(self):
        SandboxWindow(self)

    def open_history(self):
        hist = tk.Toplevel(self)
        hist.title("DATA_LOGS & AUDIT")
        hist.geometry("550x450")
        hist.configure(bg=THEME["bg"])
        txt = tk.Text(hist, font=("Consolas", 9), bg=THEME["btn_bg"], fg=THEME["fg"])
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        records = DatabaseEngine.get_history(self.user_id)
        if records:
            for r in records:
                txt.insert(tk.END, f"[{r[0]}]\nCMD: {r[1]}\nRES: {r[2]}\n{'-'*40}\n")
        else: txt.insert(tk.END, ">_ LOG BULUNAMADI.")
        txt.config(state="disabled")

# ==========================================
# 3. 5X GÜÇLENDİRİLMİŞ CAS LABORATUVARI
# ==========================================
class LabWindow(tk.Toplevel):
    def __init__(self, parent, original_text, user_id):
        super().__init__(parent)
        self.user_id = user_id
        self.title("CAS_LAB // ADVANCED_ANALYSIS")
        self.geometry("900x750")
        self.configure(bg=THEME["bg"])
        self.current_canvas = None 
        self.current_expr = None 
        
        f1 = tk.Frame(self, bg=THEME["btn_bg"], bd=1, highlightbackground=THEME["fg"], highlightthickness=1)
        f1.pack(fill="x", padx=10, pady=10)
        tk.Label(f1, text=">_ GİRDİ:", font=("Consolas", 12, "bold"), fg=THEME["fg"], bg=THEME["btn_bg"]).pack(side="left", padx=10)
        self.entry_expr = tk.Entry(f1, font=("Consolas", 14), bg=THEME["bg"], fg=THEME["accent"], insertbackground=THEME["fg"])
        self.entry_expr.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        self.entry_expr.insert(0, original_text)
        tk.Button(f1, text="[ İŞLE & ÇİZ ]", bg=THEME["bg"], fg=THEME["fg"], command=self.update_lab).pack(side="right", padx=10)

        self.graph_frame = tk.Frame(self, bg=THEME["bg"], bd=1, highlightbackground=THEME["accent"], highlightthickness=1)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 5X GÜÇLENDİRİLMİŞ BUTONLAR
        action_frame = tk.Frame(self, bg=THEME["bg"])
        action_frame.pack(fill="x", padx=10, pady=5)
        btn_st = {"font": ("Consolas", 9, "bold"), "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["accent"], "relief": "flat", "bd": 1, "highlightbackground": THEME["fg"], "highlightthickness": 1}
        
        tk.Button(action_frame, text="[ TÜREV ]", command=self.do_derivative, **btn_st).pack(side="left", expand=True, padx=1)
        tk.Button(action_frame, text="[ İNTEGRAL ]", command=self.do_integral, **btn_st).pack(side="left", expand=True, padx=1)
        tk.Button(action_frame, text="[ KÖK_BUL ]", command=self.do_solve, **btn_st).pack(side="left", expand=True, padx=1)
        tk.Button(action_frame, text="[ ÇARPANLAR ]", command=self.do_factor, **btn_st).pack(side="left", expand=True, padx=1)
        tk.Button(action_frame, text="[ SADELEŞTİR ]", command=self.do_simplify, **btn_st).pack(side="left", expand=True, padx=1)
        tk.Button(action_frame, text="[ LİMİT (x->0) ]", command=self.do_limit, **btn_st).pack(side="left", expand=True, padx=1)

        self.console = tk.Text(self, height=5, bg=THEME["btn_bg"], fg=THEME["fg"], font=("Consolas", 10), wrap="word")
        self.console.pack(fill="x", padx=10, pady=10)
        
        self.protocol("WM_DELETE_WINDOW", self.close_lab)
        self.update_lab()

    def print_to_console(self, text):
        self.console.config(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.insert(tk.END, ">_ " + text.replace("\n", "\n>_ "))
        self.console.config(state="disabled")

    def update_lab(self):
        txt = self.entry_expr.get().strip()
        try:
            is_eq, expr, roots = MathEngine.analyze_advanced(txt)
            self.current_expr = expr
            log = f"DENKLEM_ONAYLANDI\nSTANDART_FORM: {expr} = 0\nÇÖZÜM: {roots}" if is_eq else f"İFADE_ONAYLANDI\nSADE_FORM: {expr}"
            DatabaseEngine.log_session_activity(self.user_id, txt, str(roots if is_eq else expr))
            self.print_to_console(log)
            self.draw_graph(expr)
        except UnsafeExpressionException as e:
            self.print_to_console(f"GÜVENLİK_ENGELİ: {e}")
            DatabaseEngine.log_session_activity(self.user_id, txt, "BLOCKED_BY_WHITELIST")
        except Exception as e:
            self.print_to_console(f"SİSTEM_HATASI: {e}")

    def do_derivative(self):
        if not self.current_expr: return
        symbols = sorted(list(self.current_expr.free_symbols), key=lambda s: s.name)
        if symbols:
            der = sp.diff(self.current_expr, symbols[0])
            self.print_to_console(f"OP: TÜREV_ALMA\nDEĞİŞKEN: {symbols[0]}\nSONUÇ:\n{der}")

    def do_integral(self):
        if not self.current_expr: return
        symbols = sorted(list(self.current_expr.free_symbols), key=lambda s: s.name)
        if symbols:
            intg = sp.integrate(self.current_expr, symbols[0])
            self.print_to_console(f"OP: BELİRSİZ_İNTEGRAL\nDEĞİŞKEN: {symbols[0]}\nSONUÇ:\n{intg} + C")

    def do_factor(self):
        if not self.current_expr: return
        self.print_to_console(f"OP: ÇARPANLARA_AYIRMA\nSONUÇ:\n{sp.factor(self.current_expr)}")

    def do_solve(self):
        if not self.current_expr: return
        self.print_to_console(f"OP: KÖK_ANALİZİ\nÇÖZÜM_KÜMESİ:\n{sp.solve(sp.Eq(self.current_expr, 0))}")

    def do_simplify(self):
        if not self.current_expr: return
        self.print_to_console(f"OP: CEBİRSEL_SADELEŞTİRME\nSONUÇ:\n{sp.simplify(self.current_expr)}")
        
    def do_limit(self):
        if not self.current_expr: return
        symbols = sorted(list(self.current_expr.free_symbols), key=lambda s: s.name)
        if symbols:
            lim = sp.limit(self.current_expr, symbols[0], 0)
            self.print_to_console(f"OP: LİMİT_HESABI ({symbols[0]} -> 0)\nSONUÇ:\n{lim}")

    def draw_graph(self, expr):
        if self.current_canvas:
            self.current_canvas.get_tk_widget().destroy()
            plt.close('all'); gc.collect()
            
        symbols = sorted(list(expr.free_symbols), key=lambda s: s.name)
        
        if len(symbols) == 1:
            fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
            fig.patch.set_facecolor(THEME["bg"]); ax.set_facecolor(THEME["bg"])
            f_lam = sp.lambdify(symbols[0], expr, modules=['numpy'])
            x = np.linspace(-10, 10, 400); y = f_lam(x)
            if isinstance(y, (int, float)): y = np.full_like(x, y)
            ax.plot(x, y, color=THEME["fg"], linewidth=2)
            ax.axhline(0, color=THEME["accent"], linewidth=1); ax.axvline(0, color=THEME["accent"], linewidth=1)
            ax.grid(color=THEME["grid"], linestyle=':', linewidth=1)
            for spine in ax.spines.values(): spine.set_color(THEME["fg"])
            ax.tick_params(colors=THEME["fg"])
            self.current_canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            self.current_canvas.draw(); self.current_canvas.get_tk_widget().pack(fill="both", expand=True)
            
        elif len(symbols) == 2:
            fig = plt.figure(figsize=(6, 4), dpi=100)
            fig.patch.set_facecolor(THEME["bg"])
            ax = fig.add_subplot(111, projection='3d')
            ax.set_facecolor(THEME["bg"])
            f_lam = sp.lambdify((symbols[0], symbols[1]), expr, modules=['numpy'])
            X, Y = np.meshgrid(np.linspace(-10, 10, 50), np.linspace(-10, 10, 50))
            with np.errstate(all='ignore'): Z = f_lam(X, Y)
            
            ax.plot_surface(X, Y, Z, cmap='cool', alpha=0.9, edgecolor='none')
            ax.tick_params(colors=THEME["accent"])
            self.current_canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            self.current_canvas.draw(); self.current_canvas.get_tk_widget().pack(fill="both", expand=True)

    def close_lab(self):
        if self.current_canvas: plt.close('all'); gc.collect()
        self.destroy()

# ==========================================
# 4. V11 KİNETİK UZAY (CANLI BÜKÜLEN SANDBOX)
# ==========================================
class SandboxWindow(tk.Toplevel):
    def __init__(self, parent, initial_expr: str = None):
        super().__init__(parent)
        self.title("SANDBOX_SIM_STUDIO // V11 KİNETİK UZAY")
        self.geometry("1100x900")
        self.configure(bg=THEME["bg"])
        self.attributes('-topmost', True) 
        self.sb_canvas = None
        self.ani = None 
        self.is_paused = False # ZAMAN KONTROLÜ

        ctrl_frame = tk.Frame(self, bg=THEME["btn_bg"], bd=1)
        ctrl_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(ctrl_frame, text=">_ DİNAMİK BAZ (x,y,t,A,B):", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["btn_bg"]).grid(row=0, column=0, sticky="w", padx=5)
        self.ent_base = tk.Entry(ctrl_frame, font=("Consolas", 12), width=45, bg=THEME["bg"], fg=THEME["accent"], insertbackground=THEME["fg"])
        self.ent_base.grid(row=0, column=1, padx=5, pady=5)

        # Dışarıdan formül gönderilmişse onu yükle, yoksa varsayılanı kullan
        default_expr = initial_expr if initial_expr else "A * sin(x - t) * cos(y - t) + B*x"
        self.ent_base.insert(0, default_expr)

        tk.Button(ctrl_frame, text="[ EVRENİ CANLANDIR ]", font=THEME["font_main"], bg="#4A148C", fg="white", command=self.run_sandbox).grid(row=0, column=2, padx=10, pady=5)
        self.btn_pause = tk.Button(ctrl_frame, text="[ ZAMANI DURDUR ]", font=THEME["font_main"], bg=THEME["warning"], fg="black", command=self.toggle_time)
        self.btn_pause.grid(row=0, column=3, padx=10, pady=5)

        warp_frame = tk.Frame(self, bg=THEME["bg"], bd=1, highlightbackground=THEME["accent"], highlightthickness=1)
        warp_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(warp_frame, text="[ UZAY BÜKÜCÜ PARAMETRELER ]", fg="#E91E63", bg=THEME["bg"], font=THEME["font_main"]).pack(pady=2)
        
        self.val_A = tk.DoubleVar(value=1.0)
        self.val_B = tk.DoubleVar(value=0.0)
        
        slider_st = {"bg": THEME["bg"], "fg": THEME["fg"], "troughcolor": THEME["btn_bg"], "activebackground": THEME["accent"], "highlightthickness": 0}
        
        self.slider_A = tk.Scale(warp_frame, from_=-5.0, to=5.0, resolution=0.1, orient="horizontal", variable=self.val_A, label="A Katsayısı (Genlik/Yükseklik)", length=300, **slider_st)
        self.slider_A.pack(side="left", padx=20, pady=5, expand=True)
        
        self.slider_B = tk.Scale(warp_frame, from_=-2.0, to=2.0, resolution=0.1, orient="horizontal", variable=self.val_B, label="B Katsayısı (Eğim/Yerçekimi)", length=300, **slider_st)
        self.slider_B.pack(side="right", padx=20, pady=5, expand=True)

        self.sb_graph_frame = tk.Frame(self, bg="black", bd=1)
        self.sb_graph_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.sb_console = tk.Text(self, height=4, bg=THEME["btn_bg"], fg=THEME["accent"], font=("Consolas", 11, "bold"), relief="flat")
        self.sb_console.pack(fill="x", padx=10, pady=5)
        
        self.protocol("WM_DELETE_WINDOW", self.close_sandbox)

        # Dışarıdan formül gönderildiyse simülasyonu otomatik başlat
        if initial_expr:
            self.after(300, self.run_sandbox)

    def toggle_time(self):
        if self.ani:
            if self.is_paused:
                self.ani.resume()
                self.btn_pause.config(text="[ ZAMANI DURDUR ]", bg=THEME["warning"])
                self.is_paused = False
            else:
                self.ani.pause()
                self.btn_pause.config(text="[ ZAMANI BAŞLAT ]", bg=THEME["fg"])
                self.is_paused = True

    def run_sandbox(self):
        try:
            if self.ani: self.ani.event_source.stop()
            if self.sb_canvas:
                self.sb_canvas.get_tk_widget().destroy()
                plt.clf(); plt.close('all'); gc.collect()
            
            raw_expr = self.ent_base.get().strip()
            MathEngine._lexical_validation(raw_expr)
            safe_expr = MathEngine.format_input(raw_expr)
            
            self.parsed_expr = sp.parsing.sympy_parser.parse_expr(safe_expr, transformations=MathEngine.TRANSFORMATIONS)
            symbols = [s.name for s in self.parsed_expr.free_symbols]
            
            if 'x' not in symbols or 'y' not in symbols:
                messagebox.showwarning("SYS", "Canlı 3D Uzay için formülde 'x' ve 'y' değişkenleri zorunludur.")
                return

            x_sym, y_sym, t_sym, a_sym, b_sym = sp.symbols('x y t A B')
            self.f_lambdified = sp.lambdify((x_sym, y_sym, t_sym, a_sym, b_sym), self.parsed_expr, modules=['numpy'])
            
            self.fig = plt.figure(figsize=(10, 7), dpi=130)
            self.fig.patch.set_facecolor(THEME["bg"])
            self.ax = self.fig.add_subplot(111, projection='3d')
            self.ax.set_facecolor(THEME["bg"])
            
            self.X, self.Y = np.meshgrid(np.linspace(-8, 8, 60), np.linspace(-8, 8, 60))
            
            Z = self.f_lambdified(self.X, self.Y, 0, self.val_A.get(), self.val_B.get())
            self.surf = self.ax.plot_surface(self.X, self.Y, Z, cmap='magma', edgecolor='none', alpha=0.9)
            
            self.ax.tick_params(colors=THEME["accent"])
            self.ax.set_zlim(-10, 10) 
            
            self.sb_canvas = FigureCanvasTkAgg(self.fig, master=self.sb_graph_frame)
            self.sb_canvas.draw()
            self.sb_canvas.get_tk_widget().pack(fill="both", expand=True)

            self.t_val = 0.0
            def update_frame(frame):
                self.t_val += 0.15 
                A_current = self.val_A.get()
                B_current = self.val_B.get()
                
                Z_new = self.f_lambdified(self.X, self.Y, self.t_val, A_current, B_current)
                
                self.surf.remove() 
                self.surf = self.ax.plot_surface(self.X, self.Y, Z_new, cmap='magma', edgecolor='none', alpha=0.9)
                
                live_eq = self.parsed_expr.subs({'A': A_current, 'B': B_current})
                self.sb_console.config(state="normal")
                self.sb_console.delete("1.0", tk.END)
                self.sb_console.insert(tk.END, f">_ UZAY KURALI: Z = {live_eq}\n")
                self.sb_console.insert(tk.END, f">_ ANLIK MAKSİMUM DİRENÇ (Z_MAX): {np.max(Z_new):.2f}")
                self.sb_console.config(state="disabled")
                
                return self.surf,

            self.is_paused = False
            self.btn_pause.config(text="[ ZAMANI DURDUR ]", bg=THEME["warning"])
            # NOT: 3D plot_surface, blit=True'yu desteklemez (Matplotlib sınırlaması).
            # cache_frame_data=False ile gereksiz frame kopyalama engellenerek bellek tasarrufu sağlanır.
            self.ani = animation.FuncAnimation(self.fig, update_frame, interval=40, blit=False, cache_frame_data=False)

        except Exception as e:
            self.sb_console.config(state="normal")
            self.sb_console.insert(tk.END, f"\n>_ EVREN ÇÖKÜŞÜ (HATA): {str(e)}")
            self.sb_console.config(state="disabled")

    def close_sandbox(self):
        if self.ani: self.ani.event_source.stop()
        if self.sb_canvas:
            self.sb_canvas.get_tk_widget().destroy()
            plt.clf(); plt.close('all'); gc.collect()
        self.destroy()
# ==========================================
# 5. DOSYA ANALİZ MOTORU (PNG/JPG/PDF)
# ==========================================
class DocumentWindow(tk.Toplevel):
    """
    PNG / JPG / PDF dosyalarini tarayarak matematiksel ifadeleri listeler.
    Listeden secilen ifadeleri CAS Lab veya Sandbox'a gonderir.
    """

    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.parent = parent
        self.user_id = user_id
        self.title("DOSYA_ANALİZİ // OCR_SCAN_ENGINE")
        self.geometry("720x600")
        self.configure(bg=THEME["bg"])
        self.resizable(True, True)
        self.doc_engine = DocumentEngine()
        self.scan_results = []   # [{"index", "source", "equation"}]
        self.file_path = None
        self._build_ui()

    def _build_ui(self):
        # --- Başlık ---
        tk.Label(self, text=">_ DOSYA ANALİZ MOTORU // OCR PIPELINE",
                 font=("Consolas", 11, "bold"), fg=THEME["accent"],
                 bg=THEME["bg"]).pack(pady=(10, 5))

        # --- Dosya Seçim Paneli ---
        file_frame = tk.Frame(self, bg=THEME["btn_bg"], bd=1,
                              highlightbackground=THEME["fg"], highlightthickness=1)
        file_frame.pack(fill="x", padx=10, pady=5)

        btn_st = {"font": THEME["font_main"], "bg": "#00695C", "fg": "white",
                  "relief": "flat", "bd": 1, "activebackground": "#004D40"}

        tk.Button(file_frame, text="[ DOSYA_SEÇ ]",
                  command=self._select_file, **btn_st).pack(side="left", padx=10, pady=8)

        self.lbl_file = tk.Label(file_frame,
                                  text=">_ Henuz dosya secilmedi...",
                                  font=("Consolas", 9), fg=THEME["warning"],
                                  bg=THEME["btn_bg"], anchor="w")
        self.lbl_file.pack(side="left", fill="x", expand=True, padx=5)

        tk.Button(file_frame, text="[ TARA_VE_ANALİZ_ET ]",
                  command=self._start_scan,
                  font=THEME["font_main"], bg="#4A148C", fg="white",
                  relief="flat", bd=1, activebackground="#7B1FA2").pack(side="right", padx=10, pady=8)

        # --- İlerleme Çubuğu ---
        prog_frame = tk.Frame(self, bg=THEME["bg"])
        prog_frame.pack(fill="x", padx=10, pady=2)

        tk.Label(prog_frame, text=">_ TARAMA İLERLEMESİ:",
                 font=("Consolas", 8), fg=THEME["fg"],
                 bg=THEME["bg"]).pack(side="left")

        self.progress_var = tk.DoubleVar(value=0)
        self.progressbar = ttk.Progressbar(prog_frame, variable=self.progress_var,
                                            maximum=100, length=400,
                                            style="green.Horizontal.TProgressbar")
        # ttk stili
        style = ttk.Style()
        style.theme_use("default")
        style.configure("green.Horizontal.TProgressbar",
                         troughcolor=THEME["btn_bg"],
                         background=THEME["fg"], thickness=12)
        self.progressbar.pack(side="left", padx=10, fill="x", expand=True)

        self.lbl_progress = tk.Label(prog_frame, text="0%",
                                      font=("Consolas", 8), fg=THEME["fg"],
                                      bg=THEME["bg"])
        self.lbl_progress.pack(side="left")

        # --- Sonuç Listesi ---
        list_frame = tk.Frame(self, bg=THEME["bg"], bd=1,
                               highlightbackground=THEME["accent"], highlightthickness=1)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(list_frame, text=">_ BULUNAN MATEMATİKSEL İFADELER:",
                 font=("Consolas", 9, "bold"), fg=THEME["fg"],
                 bg=THEME["bg"]).pack(anchor="w", padx=5, pady=3)

        list_inner = tk.Frame(list_frame, bg=THEME["bg"])
        list_inner.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_inner, bg=THEME["btn_bg"])
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(list_inner,
                                   font=("Consolas", 10),
                                   bg=THEME["btn_bg"], fg=THEME["fg"],
                                   selectbackground=THEME["active"],
                                   selectforeground="black",
                                   activestyle="none",
                                   yscrollcommand=scrollbar.set,
                                   relief="flat", bd=0)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Çift tıklama ile CAS Lab'a gönder
        self.listbox.bind("<Double-Button-1>", lambda e: self._send_to_cas())

        # --- Alt Butonlar ---
        btn_frame = tk.Frame(self, bg=THEME["bg"])
        btn_frame.pack(fill="x", padx=10, pady=8)

        action_st = {"font": THEME["font_main"], "relief": "flat", "bd": 1}

        tk.Button(btn_frame, text="[ CAS_LAB'A_GÖNDER ]",
                  command=self._send_to_cas,
                  bg=THEME["btn_bg"], fg=THEME["fg"],
                  activebackground=THEME["accent"],
                  **action_st).pack(side="left", expand=True, padx=5, fill="x")

        tk.Button(btn_frame, text="[ SANDBOX'A_AT  🌌 ]",
                  command=self._send_to_sandbox,
                  bg="#4A148C", fg="white",
                  activebackground="#7B1FA2",
                  **action_st).pack(side="left", expand=True, padx=5, fill="x")

        tk.Button(btn_frame, text="[ LİSTEYİ_TEMİZLE ]",
                  command=self._clear_results,
                  bg=THEME["bg"], fg=THEME["error"],
                  activebackground=THEME["btn_bg"],
                  **action_st).pack(side="right", padx=5)

        # --- Durum Konsolu ---
        self.status_var = tk.StringVar(value=">_ Hazir. Dosya sec ve 'TARA' tusuna bas.")
        tk.Label(self, textvariable=self.status_var,
                 font=("Consolas", 8), fg=THEME["accent"],
                 bg=THEME["bg"], anchor="w").pack(fill="x", padx=12, pady=(0, 8))

    # ------------------------------------------------------------------
    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Dosya Sec",
            filetypes=[
                ("Desteklenen Dosyalar", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.pdf"),
                ("Goruntu Dosyalari", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("PDF Dosyalari", "*.pdf"),
                ("Tum Dosyalar", "*.*")
            ]
        )
        if path:
            self.file_path = path
            short = path if len(path) <= 55 else "..." + path[-52:]
            self.lbl_file.config(text=f">_ {short}", fg=THEME["fg"])
            self.status_var.set(f">_ Dosya yuklendi. 'TARA_VE_ANALİZ_ET' tusuna bas.")

    # ------------------------------------------------------------------
    def _start_scan(self):
        if not self.file_path:
            messagebox.showwarning("UYARI", ">_ Once bir dosya sec!")
            return
        self._clear_results()
        self.status_var.set(">_ Tarama basliyor... Lutfen bekle.")
        self.progress_var.set(0)
        # Thread'de calistir — GUI donmasin
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            def progress_cb(current, total):
                if total > 0:
                    pct = int((current / total) * 100)
                    def _upd(p=pct):
                        self.progress_var.set(p)
                        self.lbl_progress.config(text=f"{p}%")
                    self.after(0, _upd)

            results = self.doc_engine.analyze_file(self.file_path, progress_cb=progress_cb)
            self.scan_results = results

            def _populate():
                self.listbox.delete(0, tk.END)
                if not results:
                    self.listbox.insert(tk.END, ">_ OCR sonucu matematiksel ifade bulunamadi.")
                    self.status_var.set(">_ Tarama tamamlandi — ifade bulunamadi.")
                    return
                for item in results:
                    tag = f"#{item['index']}"
                    line = f"  {tag:>4}  [{item['source']}]  {item['equation']}"
                    self.listbox.insert(tk.END, line)
                self.progress_var.set(100)
                self.lbl_progress.config(text="100%")
                self.status_var.set(f">_ Tarama tamamlandi. {len(results)} ifade bulundu. Secip gonderin.")

            self.after(0, _populate)

        except DocumentError as e:
            def _err(msg=str(e)):
                self.status_var.set(f">_ HATA: {msg}")
                messagebox.showerror("DOSYA_ANALİZ_HATASI", msg)
            self.after(0, _err)
        except Exception as e:
            def _err2(msg=str(e)):
                self.status_var.set(f">_ SISTEM HATASI: {msg}")
            self.after(0, _err2)

    # ------------------------------------------------------------------
    def _get_selected_equation(self) -> str | None:
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("SECIM", ">_ Listeden bir ifade sec!")
            return None
        idx = sel[0]
        if idx >= len(self.scan_results):
            return None
        item = self.scan_results[idx]
        # index=0 sadece uyari satiriysa gec
        if item["index"] == 0:
            messagebox.showwarning("UYARI", item["equation"])
            return None
        return item["equation"]

    # ------------------------------------------------------------------
    def _send_to_cas(self):
        eq = self._get_selected_equation()
        if eq is None:
            return
        # OCR gelen ifadeyi MathEngine formatina donustur
        try:
            formatted = MathEngine.format_input(eq)
            LabWindow(self.parent, formatted, self.user_id)
            self.status_var.set(f">_ CAS Lab'a gonderildi: {formatted}")
        except Exception as e:
            messagebox.showerror("CAS_HATA", str(e))

    # ------------------------------------------------------------------
    def _send_to_sandbox(self):
        eq = self._get_selected_equation()
        if eq is None:
            return

        formatted = MathEngine.format_input(eq)

        # Sandbox uyumluluk kontrolu: x ve y olmali
        has_x = 'x' in formatted.lower()
        has_y = 'y' in formatted.lower()

        if not (has_x and has_y):
            answer = messagebox.askyesno(
                "SANDBOX_UYARI",
                f"Secilen ifade: '{formatted}'\n\n"
                f"Sandbox 3D uzay icin 'x' ve 'y' degiskeni gerektirir.\n"
                f"Bu ifade x={has_x}, y={has_y} iceriyor.\n\n"
                f"Yine de Sandbox'a gondermek ister misin?\n"
                f"(Formulu elle duzenleyebilirsin)"
            )
            if not answer:
                return

        SandboxWindow(self.parent, initial_expr=formatted)
        self.status_var.set(f">_ Sandbox'a gonderildi: {formatted}")

    # ------------------------------------------------------------------
    def _clear_results(self):
        self.scan_results = []
        self.listbox.delete(0, tk.END)
        self.progress_var.set(0)
        self.lbl_progress.config(text="0%")
        self.status_var.set(">_ Liste temizlendi.")
