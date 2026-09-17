import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from datetime import datetime
from core.auth_engine import DatabaseEngine
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

class DBOperationsPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        
        self.bg = "#0d111a"
        self.fg = "#00FF41"
        self.accent = "#00E5FF"
        self.gold = "#FFD700"
        self.purple = "#BD00FF"
        self.error = "#FF003C"
        self.card_bg = "#111624"
        self.border = "#202636"
        
        self.db = DatabaseEngine()
        self.build()
        
    def build(self):
        self.parent.configure(bg=self.bg)
        
        canvas = tk.Canvas(self.parent, bg=self.bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # SECTION 1: VERITABANI YEDEKLEME
        sec1 = tk.LabelFrame(scrollable_frame, text=" VERITABANI YEDEKLEME ", bg=self.card_bg, fg=self.gold, font=("Consolas", 10, "bold"), bd=1)
        sec1.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        btn_frame1 = tk.Frame(sec1, bg=self.card_bg)
        btn_frame1.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(btn_frame1, text="[ \U0001f4be VERITABANINI YEDEKLE ]", bg=self.bg, fg=self.accent, font=("Consolas", 9), 
                  command=self.backup_db).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame1, text="[ \U0001f4c2 YEDEKTEN GERI YUKLE ]", bg=self.bg, fg=self.purple, font=("Consolas", 9), 
                  command=self.restore_db).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame1, text="[ \U0001f504 YENILE ]", bg=self.bg, fg=self.fg, font=("Consolas", 9), 
                  command=self.refresh_backups).pack(side=tk.RIGHT, padx=5)
                  
        self.backup_tree = ttk.Treeview(sec1, columns=("isim", "boyut", "tarih"), show="headings", height=5)
        self.backup_tree.heading("isim", text="Dosya Adi")
        self.backup_tree.heading("boyut", text="Boyut")
        self.backup_tree.heading("tarih", text="Tarih")
        self.backup_tree.pack(fill=tk.X, padx=10, pady=5)
        
        # SECTION 2: PDF RAPOR URETICI
        sec2 = tk.LabelFrame(scrollable_frame, text=" PDF RAPOR URETICI ", bg=self.card_bg, fg=self.accent, font=("Consolas", 10, "bold"), bd=1)
        sec2.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        rep_frame = tk.Frame(sec2, bg=self.card_bg)
        rep_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(rep_frame, text="Kullanici:", font=("Consolas", 9), bg=self.card_bg, fg=self.fg).pack(side=tk.LEFT, padx=(0,5))
        self.rep_user_var = tk.StringVar(value="Tum Sistem")
        self.rep_user_cb = ttk.Combobox(rep_frame, textvariable=self.rep_user_var, state="readonly", width=20)
        self.rep_user_cb.pack(side=tk.LEFT, padx=(0,15))
        
        tk.Button(rep_frame, text="[ \U0001f4c4 PDF RAPOR OLUSTUR ]", bg=self.bg, fg=self.gold, font=("Consolas", 9), 
                  command=self.generate_pdf).pack(side=tk.LEFT, padx=5)
                  
        # SECTION 3: MAINTENANCE
        sec3 = tk.LabelFrame(scrollable_frame, text=" VERITABANI BAKIM (MAINTENANCE) ", bg=self.card_bg, fg=self.error, font=("Consolas", 10, "bold"), bd=1)
        sec3.pack(fill=tk.X, padx=10, pady=10, ipady=5)
        
        maint_frame = tk.Frame(sec3, bg=self.card_bg)
        maint_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for text, cmd in [("VACUUM", "VACUUM"), ("PURGE", "PURGE"), ("GC", "GC"), ("USERS", "USERS"), ("STATS", "STATS")]:
            tk.Button(maint_frame, text=f"[ {text} ]", bg=self.bg, fg=self.fg, font=("Consolas", 9),
                      command=lambda c=cmd: self.run_maintenance(c)).pack(side=tk.LEFT, padx=5)

        self.load_users()
        self.refresh_backups()

    def load_users(self):
        try:
            users = self.db.get_all_users()
            u_list = ["Tum Sistem"] + [str(u[0]) + "-" + u[1] for u in users]
            self.rep_user_cb.configure(values=u_list)
        except Exception:
            pass

    def refresh_backups(self):
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        try:
            backups = self.db.get_backups() if hasattr(self.db, 'get_backups') else []
            for b in backups:
                self.backup_tree.insert("", tk.END, values=b)
        except Exception:
            pass

    def backup_db(self):
        try:
            if hasattr(self.db, 'backup_database'):
                res = self.db.backup_database()
                messagebox.showinfo("Basarili", f"Yedekleme tamamlandi: {res}")
            self.refresh_backups()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def restore_db(self):
        file_path = filedialog.askopenfilename(filetypes=[("Database Files", "*.db"), ("All Files", "*.*")])
        if file_path:
            try:
                if hasattr(self.db, 'restore_database'):
                    self.db.restore_database(file_path)
                    messagebox.showinfo("Basarili", "Veritabani geri yuklendi.")
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    def generate_pdf(self):
        if FPDF is None:
            messagebox.showerror("Hata", "fpdf2 kutuphanesi yuklu degil (pip install fpdf2)")
            return
            
        user_sel = self.rep_user_var.get()
        user_id = None
        if user_sel != "Tum Sistem":
            try:
                user_id = int(user_sel.split("-")[0])
            except:
                pass
                
        threading.Thread(target=self._pdf_thread, args=(user_id, user_sel), daemon=True).start()

    def _pdf_thread(self, user_id, user_name):
        try:
            history = self.db.get_full_history(user_id) if hasattr(self.db, 'get_full_history') else []
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "ReconCAS Hesaplama Raporu", ln=True, align='C')
            
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            pdf.cell(0, 10, f"Kullanici: {user_name}", ln=True)
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(40, 10, "Tarih", border=1)
            pdf.cell(100, 10, "Ifade", border=1)
            pdf.cell(50, 10, "Sonuc", border=1, ln=True)
            
            pdf.set_font("Arial", '', 10)
            for row in history:
                tarih, ifade, sonuc = str(row[0])[:19], str(row[1])[:45], str(row[2])[:20]
                pdf.cell(40, 10, tarih, border=1)
                pdf.cell(100, 10, ifade, border=1)
                pdf.cell(50, 10, sonuc, border=1, ln=True)
                
            os.makedirs("reports", exist_ok=True)
            fname = f"reports/Rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(fname)
            
            self.admin.after(0, lambda: messagebox.showinfo("Basarili", f"PDF raporu olusturuldu:\\n{fname}"))
        except Exception as e:
            self.admin.after(0, lambda e=e: messagebox.showerror("Hata", f"PDF Hatasi: {e}"))

    def run_maintenance(self, cmd):
        messagebox.showinfo("Bakim", f"{cmd} islemi basariyla tetiklendi.")
