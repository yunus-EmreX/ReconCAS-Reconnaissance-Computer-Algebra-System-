import tkinter as tk
from tkinter import ttk
import psutil
import threading
import time
import os
from core.auth_engine import DatabaseEngine

class SystemMonitorPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        self.is_running = True
        self.build()
        
    def build(self):
        self.parent.configure(bg="#0d111a")
        
        lbl_header = tk.Label(self.parent, text="SISTEM MONITORU", bg="#0d111a", fg="#00E5FF", font=("Consolas", 12, "bold"))
        lbl_header.pack(pady=10)
        
        self.metrics_frame = tk.Frame(self.parent, bg="#0d111a")
        self.metrics_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.cpu_lbl = tk.Label(self.metrics_frame, text="CPU: 0%", bg="#0d111a", fg="#00FF41", font=("Consolas", 9))
        self.cpu_lbl.grid(row=0, column=0, sticky="w", pady=5)
        self.cpu_canvas = tk.Canvas(self.metrics_frame, width=300, height=15, bg="#111624", highlightthickness=1, highlightbackground="#202636")
        self.cpu_canvas.grid(row=0, column=1, padx=10)
        
        self.ram_lbl = tk.Label(self.metrics_frame, text="RAM: 0 MB / 0 MB (0%)", bg="#0d111a", fg="#00FF41", font=("Consolas", 9))
        self.ram_lbl.grid(row=1, column=0, sticky="w", pady=5)
        self.ram_canvas = tk.Canvas(self.metrics_frame, width=300, height=15, bg="#111624", highlightthickness=1, highlightbackground="#202636")
        self.ram_canvas.grid(row=1, column=1, padx=10)
        
        self.disk_lbl = tk.Label(self.metrics_frame, text="DISK: 0%", bg="#0d111a", fg="#00FF41", font=("Consolas", 9))
        self.disk_lbl.grid(row=2, column=0, sticky="w", pady=5)
        self.disk_canvas = tk.Canvas(self.metrics_frame, width=300, height=15, bg="#111624", highlightthickness=1, highlightbackground="#202636")
        self.disk_canvas.grid(row=2, column=1, padx=10)
        
        self.proc_lbl = tk.Label(self.metrics_frame, text="SUREC RSS: 0 MB", bg="#0d111a", fg="#00FF41", font=("Consolas", 9))
        self.proc_lbl.grid(row=3, column=0, sticky="w", pady=5)
        
        lbl_prof = tk.Label(self.parent, text="SON 20 OCR ISLEMI", bg="#0d111a", fg="#00E5FF", font=("Consolas", 10, "bold"))
        lbl_prof.pack(pady=(20, 5))
        
        style = ttk.Style()
        if "Cyber.Treeview" not in style.theme_names():
            style.theme_use("default")
        style.configure("Cyber.Treeview", background="#111624", foreground="#00FF41", fieldbackground="#111624", rowheight=20)
        style.map("Cyber.Treeview", background=[('selected', '#BD00FF')])
        style.configure("Cyber.Treeview.Heading", background="#202636", foreground="#00E5FF", font=("Consolas", 9, "bold"))
        
        columns = ("Time", "PSM", "Duration", "Result")
        self.tree = ttk.Treeview(self.parent, columns=columns, show="headings", style="Cyber.Treeview", height=10)
        self.tree.heading("Time", text="ZAMAN")
        self.tree.heading("PSM", text="MOD")
        self.tree.heading("Duration", text="SURE (ms)")
        self.tree.heading("Result", text="SONUC")
        self.tree.column("Time", width=150)
        self.tree.column("PSM", width=80)
        self.tree.column("Duration", width=100)
        self.tree.column("Result", width=250)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        
        self.update_profiler()

    def update_bar(self, canvas, percentage):
        canvas.delete("bar")
        width = 300 * (percentage / 100.0)
        color = "#00FF41"
        if percentage >= 80:
            color = "#FF003C"
        elif percentage >= 60:
            color = "#FFD700"
        canvas.create_rectangle(0, 0, width, 15, fill=color, tags="bar")

    def monitor_loop(self):
        process = psutil.Process(os.getpid())
        while self.is_running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                rss = process.memory_info().rss / (1024 * 1024)
                self.admin.after(0, self.update_ui, cpu, ram.used, ram.total, ram.percent, disk.percent, rss)
            except Exception:
                pass
            time.sleep(2)

    def update_ui(self, cpu, ram_used, ram_total, ram_pct, disk_pct, rss):
        if not self.is_running: return
        self.cpu_lbl.config(text=f"CPU: {cpu}%")
        self.update_bar(self.cpu_canvas, cpu)
        
        self.ram_lbl.config(text=f"RAM: {ram_used//(1024*1024)} MB / {ram_total//(1024*1024)} MB ({ram_pct}%)")
        self.update_bar(self.ram_canvas, ram_pct)
        
        self.disk_lbl.config(text=f"DISK: {disk_pct}%")
        self.update_bar(self.disk_canvas, disk_pct)
        
        self.proc_lbl.config(text=f"SUREC RSS: {rss:.1f} MB")

    def update_profiler(self):
        try:
            db = DatabaseEngine()
            if hasattr(db, 'get_session_log'):
                logs = db.get_session_log()
                ocr_logs = [log for log in logs if log.get('action') == 'OCR_SCAN']
                ocr_logs = sorted(ocr_logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:20]
                
                self.tree.delete(*self.tree.get_children())
                for log in ocr_logs:
                    details = log.get('details', {})
                    psm = details.get('psm', 'N/A')
                    duration = details.get('duration_ms', 'N/A')
                    res = details.get('result', 'N/A')
                    self.tree.insert("", "end", values=(log.get('timestamp'), psm, duration, res))
        except Exception:
            pass

    def cleanup(self):
        self.is_running = False
