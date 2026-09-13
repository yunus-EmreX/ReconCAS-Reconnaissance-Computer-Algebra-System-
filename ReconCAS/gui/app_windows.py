import tkinter as tk
from tkinter import messagebox
import threading
import time
import gc
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sympy as sp

from core.auth_engine import DatabaseEngine, AuthError
from core.math_engine import MathEngine, MathError, UnsafeExpressionException
from vision.ocr_engine import OCREngine, OCRError

THEME = {
    "bg": "#050505", "fg": "#00FF41", "btn_bg": "#111111", 
    "active": "#008F11", "accent": "#00FFFF", "grid": "#333333",
    "font_main": ("Consolas", 10, "bold"), "font_title": ("Consolas", 11, "bold"),
    "error": "#FF003C"
}

class AuthGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SYSTEM.LOGIN // V10.0")
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

class TerminalGUI(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.title("SYSTEM.CORE // V10.0 ENTERPRISE")
        self.geometry("380x280")
        self.resizable(False, False)
        self.attributes('-topmost', True) 
        self.configure(bg=THEME["bg"])
        self.is_live = False
        self.ocr = OCREngine()
        self.setup_main_menu()

    def setup_main_menu(self):
        header = tk.Frame(self, bg=THEME["bg"])
        header.pack(fill="x", pady=5)
        tk.Label(header, text=">_ AUTH: ACCEPTED | SECURE_PARSER: ACTIVE", font=("Consolas", 9), fg=THEME["accent"], bg=THEME["bg"]).pack()
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1}

        self.btn_single = tk.Button(self, text="[ ALAN_SEÇ_VE_ANALİZ_ET ]", command=lambda: self.prepare_snipping("single"), **btn_st)
        self.btn_single.pack(pady=4, padx=20, fill="x")
        
        self.btn_live_area = tk.Button(self, text="[ CANLI_BÖLGE_İZLEMESİ ]", command=lambda: self.toggle_live("live_area"), **btn_st)
        self.btn_live_area.pack(pady=4, padx=20, fill="x")

        tk.Button(self, text="[ SANDBOX_SIM_STUDIO ]", command=self.open_sandbox, font=THEME["font_main"], bg="#4A148C", fg="white", relief="flat", bd=1).pack(pady=10, padx=20, fill="x")
        tk.Button(self, text="[ İŞLEM_GEÇMİŞİ_LOGLARI ]", command=self.open_history, font=("Consolas", 9), bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack(fill="x")

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
        try:
            equations = self.ocr.extract_equations(bbox)
            if not equations: return messagebox.showwarning("SYS", "VERİ BULUNAMADI.")
            
            first_eq = equations[0]
            if MathEngine.is_advanced(first_eq):
                LabWindow(self, first_eq, self.user_id)
            else:
                res = MathEngine.evaluate_basic(first_eq)
                DatabaseEngine.log_session_activity(self.user_id, first_eq, str(res))
                messagebox.showinfo("RESULT", f"GİRDİ: {first_eq}\nÇIKTI: {res}")
        except UnsafeExpressionException as e: 
            DatabaseEngine.log_session_activity(self.user_id, first_eq, "SECURITY_BLOCK")
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
                equations = self.ocr.extract_equations(bbox, use_frame_diff=True)
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
                
                if results: self.after(0, lambda t=">_ VERİ_AKISI:\n" + "\n".join(results): self.live_text_var.set(t))
            except: pass
            time.sleep(1.0)

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

    def open_sandbox(self):
        SandboxWindow(self)

class LabWindow(tk.Toplevel):
    def __init__(self, parent, original_text, user_id):
        super().__init__(parent)
        self.user_id = user_id
        self.title("CAS_LAB // SECURE_ANALYSIS")
        self.geometry("850x750")
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
        
        action_frame = tk.Frame(self, bg=THEME["bg"])
        action_frame.pack(fill="x", padx=10, pady=5)
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["accent"], "relief": "flat", "bd": 1, "highlightbackground": THEME["fg"], "highlightthickness": 1}
        
        tk.Button(action_frame, text="[ TÜREV ]", command=self.do_derivative, **btn_st).pack(side="left", expand=True, padx=2)
        tk.Button(action_frame, text="[ İNTEGRAL ]", command=self.do_integral, **btn_st).pack(side="left", expand=True, padx=2)
        tk.Button(action_frame, text="[ ÇARPANLAR ]", command=self.do_factor, **btn_st).pack(side="left", expand=True, padx=2)
        tk.Button(action_frame, text="[ KÖK_BUL ]", command=self.do_solve, **btn_st).pack(side="left", expand=True, padx=2)

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
        else: self.print_to_console("UYARI: DEĞİŞKEN BULUNAMADI")

    def do_integral(self):
        if not self.current_expr: return
        symbols = sorted(list(self.current_expr.free_symbols), key=lambda s: s.name)
        if symbols:
            intg = sp.integrate(self.current_expr, symbols[0])
            self.print_to_console(f"OP: BELİRSİZ_İNTEGRAL\nDEĞİŞKEN: {symbols[0]}\nSONUÇ:\n{intg} + C")
        else: self.print_to_console("UYARI: DEĞİŞKEN BULUNAMADI")

    def do_factor(self):
        if not self.current_expr: return
        self.print_to_console(f"OP: ÇARPANLARA_AYIRMA\nSONUÇ:\n{sp.factor(self.current_expr)}")

    def do_solve(self):
        if not self.current_expr: return
        self.print_to_console(f"OP: KÖK_ANALİZİ\nÇÖZÜM_KÜMESİ:\n{sp.solve(sp.Eq(self.current_expr, 0))}")

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

class SandboxWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("SANDBOX_SIM_STUDIO // CUSTOM_UNIVERSE")
        self.geometry("900x800")
        self.configure(bg=THEME["bg"])
        self.attributes('-topmost', True) 
        self.sb_canvas = None

        ctrl_frame = tk.Frame(self, bg=THEME["btn_bg"], bd=1, highlightbackground=THEME["accent"], highlightthickness=1)
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(ctrl_frame, text=">_ BAZ FONKSİYON f(x,y):", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["btn_bg"]).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_base = tk.Entry(ctrl_frame, font=("Consolas", 12), width=35, bg=THEME["bg"], fg=THEME["accent"], insertbackground=THEME["fg"], relief="flat")
        self.ent_base.grid(row=0, column=1, padx=5, pady=5)
        self.ent_base.insert(0, "sin(x) * cos(y)")

        tk.Label(ctrl_frame, text=">_ UZAY BÜKÜCÜ ÇARPAN U(x,y):", font=THEME["font_main"], fg="#E91E63", bg=THEME["btn_bg"]).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ent_warp = tk.Entry(ctrl_frame, font=("Consolas", 12), width=35, bg=THEME["bg"], fg="#E91E63", insertbackground=THEME["fg"], relief="flat")
        self.ent_warp.grid(row=1, column=1, padx=5, pady=5)
        self.ent_warp.insert(0, "x^2")

        tk.Button(ctrl_frame, text="[ EVRENİ SİMÜLE ET ]", font=THEME["font_main"], bg=THEME["bg"], fg=THEME["fg"], command=self.run_sandbox).grid(row=0, column=2, rowspan=2, padx=20, pady=5, sticky="nsew")

        self.sb_graph_frame = tk.Frame(self, bg="black", bd=1, highlightbackground=THEME["fg"], highlightthickness=1)
        self.sb_graph_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.sb_console = tk.Text(self, height=6, bg=THEME["btn_bg"], fg=THEME["accent"], font=("Consolas", 10), relief="flat")
        self.sb_console.pack(fill="x", padx=10, pady=10)
        
        self.protocol("WM_DELETE_WINDOW", self.close_sandbox)
        self.run_sandbox()

    def run_sandbox(self):
        try:
            MathEngine._lexical_validation(self.ent_base.get())
            MathEngine._lexical_validation(self.ent_warp.get())
            
            base_str = MathEngine.format_input(self.ent_base.get().strip())
            warp_str = MathEngine.format_input(self.ent_warp.get().strip())
            
            base_expr = sp.parsing.sympy_parser.parse_expr(base_str, transformations=MathEngine.TRANSFORMATIONS)
            warp_expr = sp.parsing.sympy_parser.parse_expr(warp_str, transformations=MathEngine.TRANSFORMATIONS)
            custom_universe_expr = sp.simplify(base_expr * warp_expr)
            
            self.sb_console.config(state="normal"); self.sb_console.delete("1.0", tk.END)
            self.sb_console.insert(tk.END, f">_ YENİ EVREN KURULDU: Z = {custom_universe_expr}\n")
            
            if self.sb_canvas:
                self.sb_canvas.get_tk_widget().destroy()
                plt.clf(); plt.close('all'); gc.collect()
                self.sb_canvas = None

            symbols = sorted(list(custom_universe_expr.free_symbols), key=lambda s: s.name)
            
            if len(symbols) == 1:
                x_sym = symbols[0]
                f_lambdified = sp.lambdify(x_sym, custom_universe_expr, modules=['numpy'])
                x_vals = np.linspace(-10, 10, 400)
                with np.errstate(all='ignore'): y_vals = f_lambdified(x_vals)
                
                valid_y = y_vals[np.isfinite(y_vals)] 
                if len(valid_y) > 0:
                    self.sb_console.insert(tk.END, f">_ DİRENÇ TAVANI (MAX): {np.max(valid_y):.2f}\n>_ DİRENÇ TABANI (MIN): {np.min(valid_y):.2f}\n")
                
                fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
                fig.patch.set_facecolor(THEME["bg"]); ax.set_facecolor(THEME["bg"])
                ax.plot(x_vals, y_vals, color="#E91E63", linewidth=2)
                ax.axhline(0, color=THEME["fg"], linewidth=1); ax.axvline(0, color=THEME["fg"], linewidth=1)
                ax.grid(color=THEME["grid"], linestyle=':', linewidth=1)
                for spine in ax.spines.values(): spine.set_color(THEME["fg"])
                ax.tick_params(colors=THEME["fg"])
                self.sb_canvas = FigureCanvasTkAgg(fig, master=self.sb_graph_frame)
                self.sb_canvas.draw(); self.sb_canvas.get_tk_widget().pack(fill="both", expand=True)

            elif len(symbols) == 2:
                x_sym, y_sym = symbols[0], symbols[1]
                f_lambdified = sp.lambdify((x_sym, y_sym), custom_universe_expr, modules=['numpy'])
                X, Y = np.meshgrid(np.linspace(-10, 10, 50), np.linspace(-10, 10, 50))
                with np.errstate(all='ignore'): Z = f_lambdified(X, Y)
                    
                valid_z = Z[np.isfinite(Z)]
                if len(valid_z) > 0:
                    self.sb_console.insert(tk.END, f">_ KRİTİK ZİRVE (MAX Z): {np.max(valid_z):.2f}\n>_ KRİTİK ÇUKUR (MIN Z): {np.min(valid_z):.2f}\n")

                fig = plt.figure(figsize=(6, 4), dpi=100)
                fig.patch.set_facecolor(THEME["bg"])
                ax = fig.add_subplot(111, projection='3d')
                ax.set_facecolor(THEME["bg"])
                ax.plot_surface(X, Y, Z, cmap='magma', alpha=0.9, edgecolor='none')
                ax.tick_params(colors=THEME["accent"])
                self.sb_canvas = FigureCanvasTkAgg(fig, master=self.sb_graph_frame)
                self.sb_canvas.draw(); self.sb_canvas.get_tk_widget().pack(fill="both", expand=True)
            else:
                self.sb_console.insert(tk.END, ">_ HATA: LÜTFEN SADECE 1 VEYA 2 DEĞİŞKEN KULLANIN.\n")
            self.sb_console.config(state="disabled")

        except UnsafeExpressionException as e:
            self.sb_console.config(state="normal")
            self.sb_console.insert(tk.END, f"\n>_ GÜVENLİK BLOKAJI: {e}")
            self.sb_console.config(state="disabled")
        except Exception as e:
            self.sb_console.config(state="normal")
            self.sb_console.insert(tk.END, f"\n>_ EVREN ÇÖKÜŞÜ (HATA): {e}")
            self.sb_console.config(state="disabled")

    def close_sandbox(self):
        if self.sb_canvas:
            self.sb_canvas.get_tk_widget().destroy()
            plt.clf(); plt.close('all'); gc.collect()
            self.sb_canvas = None
        self.destroy()