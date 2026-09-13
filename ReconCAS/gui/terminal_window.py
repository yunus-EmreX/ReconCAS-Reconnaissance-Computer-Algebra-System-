import tkinter as tk
from tkinter import messagebox
import threading
import time
from core.auth_engine import DatabaseEngine
from core.math_engine import MathEngine, UnsafeExpressionException
from vision.ocr_engine import OCREngine
from gui.theme import THEME
from gui.widgets import AnimatedToggle
from gui.lab_window import LabWindow
from gui.sandbox_window import SandboxWindow
from gui.document_window import DocumentWindow

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
        
        # 1. Overlay'i derhal gizle ve Windows DWM'nin ekranı tazelemesine izin ver
        try:
            self.overlay.withdraw()
            self.overlay.update_idletasks()
        except Exception:
            pass
        time.sleep(0.06)

        if x2 - x1 > 10 and y2 - y1 > 10:
            bbox = (x1, y1, x2, y2)
            if self.current_mode == "single":
                # ReconCAS ana penceresi deiconify EDİLMEDEN önce ekranı yakala
                self.process_single(bbox)
            else:
                self.start_live_mode(bbox)
        else:
            self.deiconify()

        try:
            self.overlay.destroy()
        except Exception:
            pass

    def cancel_snipping(self):
        try:
            self.overlay.destroy()
        except Exception:
            pass
        self.deiconify()

    def process_single(self, bbox):
        first_eq = None
        try:
            # Ekran görüntüsü ReconCAS ana penceresi henüz gizliyken alınır
            equations = self.ocr.extract_equations(bbox, debug=self.debug_mode)
            
            # Görüntü hafızaya alındıktan sonra terminali geri getir
            self.deiconify()
            
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
            self.deiconify()
            eq_label = first_eq if first_eq is not None else "<tanımsız>"
            DatabaseEngine.log_session_activity(self.user_id, eq_label, "SECURITY_BLOCK")
            messagebox.showerror("SECURITY_BLOCK", str(e))
        except Exception as e:
            self.deiconify()
            messagebox.showerror("ERROR", str(e))

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

