import tkinter as tk
from tkinter import messagebox
import gc
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import numpy as np
import sympy as sp
from core.math_engine import MathEngine
from gui.theme import THEME

class SandboxWindow(tk.Toplevel):
    def __init__(self, parent, initial_expr: str = None):
        super().__init__(parent)
        self.title("SANDBOX_SIM_STUDIO // V11 KİNETİK UZAY")
        self.geometry("1100x900")
        self.configure(bg=THEME["bg"])
        self.attributes('-topmost', True) 
        self.sb_canvas = None
        self.ani = None 
        self.is_paused = False

        ctrl_frame = tk.Frame(self, bg=THEME["btn_bg"], bd=1)
        ctrl_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(ctrl_frame, text=">_ DİNAMİK BAZ (x,y,t,A,B):", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["btn_bg"]).grid(row=0, column=0, sticky="w", padx=5)
        self.ent_base = tk.Entry(ctrl_frame, font=("Consolas", 12), width=45, bg=THEME["bg"], fg=THEME["accent"], insertbackground=THEME["fg"])
        self.ent_base.grid(row=0, column=1, padx=5, pady=5)

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

