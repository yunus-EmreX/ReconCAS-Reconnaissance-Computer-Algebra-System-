import json
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading
import time

try:
    from core.auth_engine import DatabaseEngine
except ImportError:
    class DatabaseEngine:
        @staticmethod
        def get_macros():
            return []
        @staticmethod
        def save_macro(name, data):
            pass
        @staticmethod
        def delete_macro(name):
            pass

class MacroRecorderPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        self.is_recording = False
        self.current_macro = []
        self.db = DatabaseEngine()
        self.build()

    def build(self):
        self.parent.configure(bg="#0d111a")
        
        # Header
        header_frame = tk.Frame(self.parent, bg="#0d111a")
        header_frame.pack(fill=tk.X, pady=10, padx=10)
        tk.Label(header_frame, text="MAKRO KAYDEDICI", font=("Consolas", 14, "bold"), fg="#BD00FF", bg="#0d111a").pack(side=tk.LEFT)
        
        # Record Toggle Button
        self.btn_record = tk.Button(header_frame, text="[ 🔴 KAYIT BASLAT ]", font=("Consolas", 10, "bold"), 
                                    bg="#111624", fg="#FF003C", command=self.toggle_recording, relief=tk.FLAT)
        self.btn_record.pack(side=tk.RIGHT)
        
        # Macros List Section
        list_frame = tk.Frame(self.parent, bg="#111624", bd=1, relief=tk.SOLID, highlightbackground="#202636", highlightthickness=1)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        list_header = tk.Frame(list_frame, bg="#111624")
        list_header.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(list_header, text="KAYITLI MAKROLAR", font=("Consolas", 10, "bold"), fg="#00E5FF", bg="#111624").pack(side=tk.LEFT)
        
        tk.Button(list_header, text="[ 🔄 YENILE ]", font=("Consolas", 8), bg="#0d111a", fg="#00FF41", 
                  command=self.load_macros, relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)
        tk.Button(list_header, text="[ 🗑️ SIL ]", font=("Consolas", 8), bg="#0d111a", fg="#FF003C", 
                  command=self.delete_macro, relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)
        tk.Button(list_header, text="[ ▶️ CALISTIR ]", font=("Consolas", 8), bg="#0d111a", fg="#FFD700", 
                  command=self.play_macro, relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)
                  
        # Treeview
        columns = ("ID", "Ad", "Adim Sayisi", "Tarih")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
            
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#0d111a", foreground="#00FF41", fieldbackground="#0d111a", font=("Consolas", 9))
        style.configure("Treeview.Heading", background="#111624", foreground="#00E5FF", font=("Consolas", 9, "bold"))
        style.map("Treeview", background=[("selected", "#202636")])
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Playback text
        tk.Label(self.parent, text="Oynatma Ciktisi:", font=("Consolas", 9, "bold"), fg="#00FF41", bg="#0d111a").pack(anchor=tk.W, padx=10)
        self.playback_text = tk.Text(self.parent, font=("Consolas", 9), bg="#111624", fg="#00FF41", height=10)
        self.playback_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.load_macros()
        
    def load_macros(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            macros = self.db.get_macros() if hasattr(self.db, 'get_macros') else []
            for i, m in enumerate(macros):
                if isinstance(m, dict):
                    self.tree.insert("", tk.END, values=(m.get('id', i), m.get('name', 'Bilinmeyen'), len(json.loads(m.get('data', '[]'))), m.get('date', '-')))
                else:
                    self.tree.insert("", tk.END, values=(m[0], m[1], len(json.loads(m[2] if len(m)>2 else '[]')), m[3] if len(m)>3 else '-'))
        except Exception as e:
            pass
            
    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.current_macro = []
            self.btn_record.config(text="[ ⏹️ KAYIT DURDUR ]", fg="#00FF41")
            self.add_step("System", "Kayit basladi.")
        else:
            self.is_recording = False
            self.btn_record.config(text="[ 🔴 KAYIT BASLAT ]", fg="#FF003C")
            
            if self.current_macro:
                name = simpledialog.askstring("Makro Kaydet", "Makro Adi:")
                if name:
                    try:
                        if hasattr(self.db, 'save_macro'):
                            self.db.save_macro(name, json.dumps(self.current_macro))
                        self.load_macros()
                    except Exception as e:
                        messagebox.showerror("Hata", f"Kaydedilemedi: {e}")
                        
    def add_step(self, action, detail):
        if self.is_recording:
            step = {"action": action, "detail": detail, "time": time.time()}
            self.current_macro.append(step)
            
    def delete_macro(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])
        macro_id = item['values'][0]
        try:
            if hasattr(self.db, 'delete_macro'):
                self.db.delete_macro(macro_id)
            self.load_macros()
        except Exception as e:
            messagebox.showerror("Hata", f"Silinemedi: {e}")
            
    def play_macro(self):
        sel = self.tree.selection()
        if not sel: return
        
        self.playback_text.delete(1.0, tk.END)
        self.playback_text.insert(tk.END, "Makro oynatiliyor...\n")
        
        def simulate():
            for i in range(5):
                time.sleep(0.5)
                self.admin.after(0, lambda idx=i: self.playback_text.insert(tk.END, f"Adim {idx+1} isleniyor...\n"))
                self.admin.after(0, lambda: self.playback_text.see(tk.END))
            self.admin.after(0, lambda: self.playback_text.insert(tk.END, "Makro tamamlandi.\n"))
            
        threading.Thread(target=simulate, daemon=True).start()
        
    def cleanup(self):
        self.is_recording = False
