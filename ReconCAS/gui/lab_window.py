import tkinter as tk
import gc
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sympy as sp
from core.auth_engine import DatabaseEngine
from core.math_engine import MathEngine, MathError, UnsafeExpressionException
from gui.theme import THEME

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

