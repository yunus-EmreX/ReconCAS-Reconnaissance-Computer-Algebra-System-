import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
from core.document_engine import DocumentEngine, DocumentError, MAX_PDF_PAGES
from core.math_engine import MathEngine
from gui.theme import THEME
from gui.lab_window import LabWindow
from gui.sandbox_window import SandboxWindow

class DocumentWindow(tk.Toplevel):
    """
    PNG / JPG / BMP / TIFF / PDF dosyalarini tarayarak matematiksel ifadeleri listeler.
    Listeden secilen ifadeleri CAS Lab veya Sandbox'a gonderir.
    """

    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.parent = parent
        self.user_id = user_id
        self.title("DOSYA_ANALİZİ // OCR_SCAN_ENGINE")
        self.geometry("780x640")
        self.configure(bg=THEME["bg"])
        self.resizable(True, True)
        self.doc_engine = DocumentEngine()
        self.scan_results = []
        self.file_path = None
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text=">_ DOSYA ANALİZ MOTORU // OCR PIPELINE",
                 font=("Consolas", 11, "bold"), fg=THEME["accent"],
                 bg=THEME["bg"]).pack(pady=(10, 5))

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

        # BUG-013: Sayfa sınırı uyarı paneli
        self.lbl_page_warning = tk.Label(self, text="", font=("Consolas", 9, "bold"),
                                         fg=THEME["warning"], bg=THEME["bg"])
        self.lbl_page_warning.pack(fill="x", padx=10, pady=(2, 0))

        prog_frame = tk.Frame(self, bg=THEME["bg"])
        prog_frame.pack(fill="x", padx=10, pady=2)

        tk.Label(prog_frame, text=">_ TARAMA İLERLEMESİ:",
                 font=("Consolas", 8), fg=THEME["fg"],
                 bg=THEME["bg"]).pack(side="left")

        self.progress_var = tk.DoubleVar(value=0)
        self.progressbar = ttk.Progressbar(prog_frame, variable=self.progress_var,
                                            maximum=100, length=400,
                                            style="green.Horizontal.TProgressbar")
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

        self.listbox.bind("<Double-Button-1>", lambda e: self._send_to_cas())

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

        self.status_var = tk.StringVar(value=">_ Hazir. Dosya sec ve 'TARA' tusuna bas.")
        tk.Label(self, textvariable=self.status_var,
                 font=("Consolas", 8), fg=THEME["accent"],
                 bg=THEME["bg"], anchor="w").pack(fill="x", padx=12, pady=(0, 8))

    def _select_file(self):
        # BUG-014: Desteklenen tüm dosya formatları
        path = filedialog.askopenfilename(
            title="Dosya Seç",
            filetypes=[
                ("Desteklenen Tüm Dosyalar", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.pdf"),
                ("PDF Dosyaları (*.pdf)", "*.pdf"),
                ("Görüntü Dosyaları (*.png;*.jpg;*.bmp;*.tiff)", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("Tüm Dosyalar (*.*)", "*.*")
            ]
        )
        if path:
            self.file_path = path
            short = path if len(path) <= 55 else "..." + path[-52:]
            self.lbl_file.config(text=f">_ {short}", fg=THEME["fg"])
            self.status_var.set(f">_ Dosya yüklendi. 'TARA_VE_ANALİZ_ET' tuşuna bas.")
            self.lbl_page_warning.config(text="")

    def _start_scan(self):
        if not self.file_path:
            messagebox.showwarning("UYARI", ">_ Önce bir dosya seç!")
            return
        self._clear_results()
        self.status_var.set(">_ Tarama başlıyor... Lütfen bekle.")
        self.progress_var.set(0)
        self.lbl_page_warning.config(text="")
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
                    self.listbox.insert(tk.END, ">_ OCR sonucu matematiksel ifade bulunamadı.")
                    self.status_var.set(">_ Tarama tamamlandı — ifade bulunamadı.")
                    return

                # BUG-013: 30 sayfa uyarı kontrolü
                actual_items = 0
                for item in results:
                    if item.get("index") == 0:
                        self.lbl_page_warning.config(text=item["equation"])
                        continue

                    actual_items += 1
                    tag = f"#{item['index']}"
                    conf_str = f" [Güven: {item.get('confidence', 0)}%]" if 'confidence' in item else ""
                    valid_mark = "" if item.get("is_valid", True) else " [DÜZELTİLEMEDİ]"
                    line = f"  {tag:>4}  [{item['source']}]  {item['equation']}{conf_str}{valid_mark}"
                    self.listbox.insert(tk.END, line)

                self.progress_var.set(100)
                self.lbl_progress.config(text="100%")
                self.status_var.set(f">_ Tarama tamamlandı. {actual_items} geçerli ifade bulundu. Seçip gönderin.")

            self.after(0, _populate)

        except DocumentError as e:
            def _err(msg=str(e)):
                self.status_var.set(f">_ HATA: {msg}")
                messagebox.showerror("DOSYA_ANALİZ_HATASI", msg)
            self.after(0, _err)
        except Exception as e:
            def _err2(msg=str(e)):
                self.status_var.set(f">_ SİSTEM HATASI: {msg}")
            self.after(0, _err2)

    def _get_selected_equation(self) -> str | None:
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("SEÇİM", ">_ Listeden bir ifade seç!")
            return None
        idx = sel[0]
        # Eğer ilk satır uyarı ise scan_results ile listbox indeks eşlemesini kontrol et
        filtered_results = [r for r in self.scan_results if r.get("index") != 0]
        if idx >= len(filtered_results):
            return None
        item = filtered_results[idx]
        return item["equation"]

    def _send_to_cas(self):
        eq = self._get_selected_equation()
        if eq is None:
            return
        try:
            formatted = MathEngine.format_input(eq)
            LabWindow(self.parent, formatted, self.user_id)
            self.status_var.set(f">_ CAS Lab'a gönderildi: {formatted}")
        except Exception as e:
            messagebox.showerror("CAS_HATA", str(e))

    def _send_to_sandbox(self):
        eq = self._get_selected_equation()
        if eq is None:
            return

        formatted = MathEngine.format_input(eq)
        has_x = 'x' in formatted.lower()
        has_y = 'y' in formatted.lower()

        if not (has_x and has_y):
            answer = messagebox.askyesno(
                "SANDBOX_UYARI",
                f"Seçilen ifade: '{formatted}'\n\n"
                f"Sandbox 3D uzay için 'x' ve 'y' değişkeni gerektirir.\n"
                f"Bu ifade x={has_x}, y={has_y} içeriyor.\n\n"
                f"Yine de Sandbox'a göndermek ister misin?\n"
                f"(Formülü elle düzenleyebilirsin)"
            )
            if not answer:
                return

        SandboxWindow(self.parent, initial_expr=formatted)
        self.status_var.set(f">_ Sandbox'a gönderildi: {formatted}")

    def _clear_results(self):
        self.scan_results = []
        self.listbox.delete(0, tk.END)
        self.progress_var.set(0)
        self.lbl_progress.config(text="0%")
        self.lbl_page_warning.config(text="")
        self.status_var.set(">_ Liste temizlendi.")

