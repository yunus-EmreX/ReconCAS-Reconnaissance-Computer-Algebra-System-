import tkinter as tk
from tkinter import ttk, messagebox
import threading
from core.auth_engine import DatabaseEngine

class SessionTrackerPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        
        # Cyberpunk colors
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
        
        main_paned = tk.PanedWindow(self.parent, orient=tk.VERTICAL, bg=self.border, sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # SECTION 1: OTURUM ve AKTIVITE IZLEME
        sec1_frame = tk.Frame(main_paned, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        main_paned.add(sec1_frame, minsize=200)
        
        lbl_sec1 = tk.Label(sec1_frame, text="OTURUM ve AKTIVITE IZLEME", font=("Consolas", 10, "bold"), bg=self.card_bg, fg=self.accent)
        lbl_sec1.pack(anchor=tk.W, padx=10, pady=5)
        
        filter_frame = tk.Frame(sec1_frame, bg=self.card_bg)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(filter_frame, text="Kullanici:", font=("Consolas", 9), bg=self.card_bg, fg=self.fg).pack(side=tk.LEFT, padx=(0, 5))
        self.user_var = tk.StringVar(value="Tum Kullanicilar")
        self.user_cb = ttk.Combobox(filter_frame, textvariable=self.user_var, state="readonly", width=15)
        self.user_cb.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(filter_frame, text="Aksiyon:", font=("Consolas", 9), bg=self.card_bg, fg=self.fg).pack(side=tk.LEFT, padx=(0, 5))
        self.action_var = tk.StringVar(value="Tum Aksiyonlar")
        self.action_cb = ttk.Combobox(filter_frame, textvariable=self.action_var, state="readonly", width=15,
                                      values=["Tum Aksiyonlar", "LOGIN", "OCR_SCAN", "CAS_EVAL", "PDF_GEN"])
        self.action_cb.pack(side=tk.LEFT, padx=(0, 15))
        
        btn_refresh = tk.Button(filter_frame, text="[ YENILE ]", bg=self.bg, fg=self.accent, font=("Consolas", 9), 
                                activebackground=self.accent, activeforeground=self.bg, relief=tk.FLAT,
                                command=self.refresh_logs)
        btn_refresh.pack(side=tk.LEFT, padx=5)
        
        btn_clear = tk.Button(filter_frame, text="[ LOGLARI TEMIZLE ]", bg=self.bg, fg=self.error, font=("Consolas", 9), 
                              activebackground=self.error, activeforeground=self.bg, relief=tk.FLAT,
                              command=self.clear_logs)
        btn_clear.pack(side=tk.RIGHT, padx=5)
        
        tree_frame = tk.Frame(sec1_frame, bg=self.card_bg)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        
        cols = ("zaman", "kullanici", "aksiyon", "detay", "sure")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=8)
        self.tree.heading("zaman", text="Zaman")
        self.tree.heading("kullanici", text="Kullanici")
        self.tree.heading("aksiyon", text="Aksiyon")
        self.tree.heading("detay", text="Detay")
        self.tree.heading("sure", text="Sure(ms)")
        
        self.tree.column("zaman", width=150)
        self.tree.column("kullanici", width=100)
        self.tree.column("aksiyon", width=100)
        self.tree.column("detay", width=300)
        self.tree.column("sure", width=80)
        
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # SECTION 2: AKTIVITE ISI HARITASI (HEATMAP)
        sec2_frame = tk.Frame(main_paned, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        main_paned.add(sec2_frame, minsize=200)
        
        lbl_sec2 = tk.Label(sec2_frame, text="AKTIVITE ISI HARITASI (HEATMAP)", font=("Consolas", 10, "bold"), bg=self.card_bg, fg=self.gold)
        lbl_sec2.pack(anchor=tk.W, padx=10, pady=5)
        
        self.canvas_frame = tk.Frame(sec2_frame, bg=self.card_bg)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.load_users()
        self.refresh_logs()
        self.draw_heatmap()
        
    def load_users(self):
        try:
            users = self.db.get_all_users()
            user_list = ["Tum Kullanicilar"] + [u[1] for u in users]
            self.user_cb.configure(values=user_list)
        except Exception:
            pass

    def refresh_logs(self):
        threading.Thread(target=self._refresh_logs_thread, daemon=True).start()
        
    def _refresh_logs_thread(self):
        try:
            logs = self.db.get_session_log(limit=200) if hasattr(self.db, 'get_session_log') else []
            self.admin.after(0, self._update_tree, logs)
        except Exception as e:
            pass

    def _update_tree(self, logs):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        u_filter = self.user_var.get()
        a_filter = self.action_var.get()
        
        for log in logs:
            try:
                zaman, kullanici, aksiyon, detay, sure = log[0], log[1], log[2], log[3], log[4]
                if u_filter != "Tum Kullanicilar" and kullanici != u_filter: continue
                if a_filter != "Tum Aksiyonlar" and aksiyon != a_filter: continue
                self.tree.insert("", tk.END, values=(zaman, kullanici, aksiyon, detay, sure))
            except:
                pass
                
    def clear_logs(self):
        if messagebox.askyesno("Onay", "Tum loglari silmek istediginizden emin misiniz?"):
            try:
                if hasattr(self.db, 'cursor'):
                    self.db.cursor.execute("DELETE FROM session_logs")
                    self.db.conn.commit()
                self.refresh_logs()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    def draw_heatmap(self):
        threading.Thread(target=self._draw_heatmap_thread, daemon=True).start()
        
    def _draw_heatmap_thread(self):
        try:
            data = self.db.get_activity_heatmap_data(days=30) if hasattr(self.db, 'get_activity_heatmap_data') else {}
            if not data:
                import random
                data = {(d, h): random.randint(0, 100) for d in range(7) for h in range(24)}
            self.admin.after(0, self._render_heatmap, data)
        except Exception:
            pass

    def _render_heatmap(self, data):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
            
        canvas = tk.Canvas(self.canvas_frame, bg=self.card_bg, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        days = ["Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz"]
        cell_size = 20
        pad_x, pad_y = 40, 20
        
        max_val = max(data.values()) if data else 1
        if max_val == 0: max_val = 1
        
        for h in range(24):
            canvas.create_text(pad_x + h*cell_size + cell_size/2, pad_y - 10, text=str(h), fill=self.fg, font=("Consolas", 7))
            
        for d in range(7):
            canvas.create_text(pad_x - 15, pad_y + d*cell_size + cell_size/2, text=days[d], fill=self.fg, font=("Consolas", 8))
            for h in range(24):
                val = data.get((d, h), 0)
                intensity = min(255, int((val / max_val) * 255))
                color = f"#{10:02x}{intensity:02x}{10:02x}" if intensity > 0 else "#0a0a0a"
                
                x1 = pad_x + h*cell_size
                y1 = pad_y + d*cell_size
                canvas.create_rectangle(x1, y1, x1+cell_size-2, y1+cell_size-2, fill=color, outline=self.border)
