# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import gc
from datetime import datetime
from core.auth_engine import DatabaseEngine
from gui.theme import THEME

# Import panels
from gui.root_panels.system_monitor import SystemMonitorPanel
from gui.root_panels.ocr_calibrator import OCRCalibratorPanel
from gui.root_panels.session_tracker import SessionTrackerPanel
from gui.root_panels.db_operations import DBOperationsPanel
from gui.root_panels.theme_engine import ThemeEnginePanel
from gui.root_panels.world_map import WorldMapPanel
from gui.root_panels.kill_switch import KillSwitchPanel
from gui.root_panels.plugin_system import PluginSystemPanel
from gui.root_panels.steganography import SteganographyPanel
from gui.root_panels.macro_recorder import MacroRecorderPanel

class AdminPuppetWindow(tk.Toplevel):
    """
    ReconCAS Superuser Control Matrix (V0.1.4 MEGA PATCH)
    14 yeni operasyonel ozellikli moduler sidebar mimarisi.
    """

    def __init__(self, parent, user_id=0):
        super().__init__(parent)
        self.parent = parent
        self.user_id = user_id
        self.title("RECON_CAS // SUPERUSER CONTROL MATRIX [GOD_MODE: ACTIVE]")
        self.geometry("1100x800")
        self.minsize(1024, 768)
        self.configure(bg="#07080d")
        
        self.is_running = True
        
        # Panel storage
        self.panels = {}
        self.active_panel_id = None
        self.active_panel_obj = None
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._start_clock()

    def _build_ui(self):
        # 1. TOP BAR
        top_bar = tk.Frame(self, bg="#0d111a", bd=1, relief="solid", highlightbackground="#BD00FF", highlightthickness=1)
        top_bar.pack(fill="x", padx=10, pady=(10, 5))

        title_box = tk.Frame(top_bar, bg="#0d111a")
        title_box.pack(side="left", padx=12, pady=8)

        tk.Label(title_box, text="👑 RECON_CAS // SUPERUSER PUPPET MATRIX", 
                 font=("Consolas", 12, "bold"), fg="#FFD700", bg="#0d111a").pack(anchor="w")
        tk.Label(title_box, text="SECURITY RING-0 // GOD_MODE: ENGAGED // MODULAR ARCHITECTURE", 
                 font=("Consolas", 8), fg="#00FF41", bg="#0d111a").pack(anchor="w")

        right_box = tk.Frame(top_bar, bg="#0d111a")
        right_box.pack(side="right", padx=12, pady=8)

        self.lbl_clock = tk.Label(right_box, text="--:--:--", font=("Consolas", 10, "bold"), fg="#00E5FF", bg="#0d111a")
        self.lbl_clock.pack(side="right")
        
        # 2. MAIN SPLIT (Sidebar + Content)
        main_frame = tk.Frame(self, bg="#07080d")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # SIDEBAR
        self.sidebar = tk.Frame(main_frame, bg="#0d111a", bd=1, relief="solid", highlightbackground="#202636", highlightthickness=1, width=220)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)
        
        # CONTENT AREA
        self.content_area = tk.Frame(main_frame, bg="#07080d")
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # Sidebar Buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("system", "🖥️ SISTEM MONTIORU", SystemMonitorPanel),
            ("ocr", "🔍 OCR KALIBRASYON", OCRCalibratorPanel),
            ("session", "👥 OTURUM IZLEME", SessionTrackerPanel),
            ("db", "🗄️ VERITABANI", DBOperationsPanel),
            ("map", "🌐 NETWORK HARITASI", WorldMapPanel),
            ("theme", "🎨 TEMA MOTORU", ThemeEnginePanel),
            ("plugin", "🧩 PLUGIN SISTEMI", PluginSystemPanel),
            ("macro", "🤖 MAKRO KAYDEDICI", MacroRecorderPanel),
            ("steg", "🕵️ STEGANOGRAFI", SteganographyPanel),
            ("kill", "🔴 KILL SWITCH", KillSwitchPanel)
        ]
        
        for p_id, text, p_class in nav_items:
            btn = tk.Button(self.sidebar, text=text, font=("Consolas", 10, "bold"),
                            bg="#111624", fg="#00E5FF", relief="flat", bd=0, anchor="w", padx=10, pady=8,
                            command=lambda i=p_id: self.load_panel(i))
            btn.pack(fill="x", pady=2, padx=4)
            
            if p_id == "kill":
                btn.configure(bg="#330000", fg="#FF003C", activebackground="#FF003C", activeforeground="white")
                
            self.nav_buttons[p_id] = btn
            self.panels[p_id] = {"class": p_class, "instance": None, "frame": None}
            
        # Load first panel
        self.load_panel("system")
        
        # 3. BOTTOM BAR
        bottom_bar = tk.Frame(self, bg="#07080d")
        bottom_bar.pack(fill="x", padx=10, pady=(2, 6))

        tk.Label(bottom_bar, text="RECON_CAS_ROOT_SESSION // RUNTIME PRIVILEGE: UNRESTRICTED // VER 0.1.4-BETA",
                 font=("Consolas", 8), fg="#555555", bg="#07080d").pack(side="left")

        tk.Button(bottom_bar, text="[ KONSOLU KAPAT ]", font=("Consolas", 8, "bold"),
                  bg="#111624", fg="#AAAAAA", relief="flat", command=self._on_close).pack(side="right")

    def load_panel(self, panel_id):
        # Reset button styles
        for pid, btn in self.nav_buttons.items():
            if pid == "kill":
                btn.configure(bg="#330000", fg="#FF003C")
            else:
                btn.configure(bg="#111624", fg="#00E5FF")
                
        # Highlight active
        if panel_id == "kill":
            self.nav_buttons[panel_id].configure(bg="#FF003C", fg="white")
        else:
            self.nav_buttons[panel_id].configure(bg="#00E5FF", fg="#0d111a")
            
        # Hide current panel
        if self.active_panel_id and self.active_panel_id in self.panels:
            old_p = self.panels[self.active_panel_id]
            if old_p["frame"]:
                old_p["frame"].pack_forget()
            # Call cleanup if exists
            if old_p["instance"] and hasattr(old_p["instance"], "cleanup"):
                old_p["instance"].cleanup()
                
        self.active_panel_id = panel_id
        p_data = self.panels[panel_id]
        
        # Instantiate if not exists
        if not p_data["frame"]:
            frame = tk.Frame(self.content_area, bg="#07080d")
            p_data["frame"] = frame
            # Try passing self as admin_window
            try:
                p_data["instance"] = p_data["class"](frame, self)
            except Exception as e:
                tk.Label(frame, text=f"PANEL YUKLENIRKEN HATA OLUSTU:\n{e}", 
                         fg="#FF003C", bg="#07080d", font=("Consolas", 10)).pack(pady=20)
                
        self.active_panel_obj = p_data["instance"]
        p_data["frame"].pack(fill="both", expand=True)
        
        # Call on_show if exists
        if hasattr(self.active_panel_obj, "on_show"):
            self.active_panel_obj.on_show()

    def _start_clock(self):
        def _loop():
            while self.is_running:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    self.after(0, lambda n=now_str: self._update_clock(n))
                except Exception:
                    break
                time.sleep(1.0)
        threading.Thread(target=_loop, daemon=True).start()

    def _update_clock(self, now_str):
        if hasattr(self, 'lbl_clock') and self.lbl_clock:
            self.lbl_clock.configure(text=now_str)

    def _on_close(self):
        self.is_running = False
        # Cleanup all panels
        for pid, p_data in self.panels.items():
            if p_data["instance"] and hasattr(p_data["instance"], "cleanup"):
                try:
                    p_data["instance"].cleanup()
                except:
                    pass
        self.destroy()
