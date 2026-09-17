import tkinter as tk
from tkinter import messagebox, simpledialog
import hashlib
from core.auth_engine import DatabaseEngine

class KillSwitchPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        self.is_running = True
        self.build()
        
    def build(self):
        self.parent.configure(bg="#0d111a")
        
        frame = tk.Frame(self.parent, bg="#111624", highlightthickness=2, highlightbackground="#FF003C")
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        lbl_warn = tk.Label(frame, text="DIKKAT!\nBU BUTON SISTEMI KILITLER", bg="#111624", fg="#FF003C", font=("Consolas", 14, "bold"))
        lbl_warn.pack(padx=20, pady=(20,10))
        
        btn = tk.Button(frame, text="🔴 SISTEM KILIDI - KILL SWITCH", bg="#FF003C", fg="white", font=("Consolas", 14, "bold"), command=self.trigger_kill_switch)
        btn.pack(padx=20, pady=(10,20))

    def trigger_kill_switch(self):
        if not messagebox.askyesno("ONAY 1", "Sistemi kilitlemek istediginize emin misiniz?"):
            return
        if not messagebox.askyesno("ONAY 2", "BU ISLEM GERI ALINAMAZ (SIFRE GEREKTIRIR). DEVAM MI?"):
            return
            
        pwd = simpledialog.askstring("Guvenlik", "Root sifresini girin:", show="*")
        if not pwd:
            return
            
        salt = '_RECON_SECURE_SALT_V1_'
        hashed = hashlib.sha256((pwd + salt).encode()).hexdigest()
        
        db = DatabaseEngine()
        if hasattr(db, '_R_P') and hashed == db._R_P:
            if hasattr(db, 'log_session'):
                db.log_session('SYSTEM_LOCKDOWN', {})
            self.lockdown()
        else:
            messagebox.showerror("HATA", "Hatali Sifre!")

    def lockdown(self):
        for widget in self.admin.winfo_children():
            try:
                widget.configure(state="disabled")
            except:
                pass
                
        self.overlay = tk.Toplevel(self.admin)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.configure(bg="#000000")
        self.overlay.protocol("WM_DELETE_WINDOW", lambda: None)
        self.overlay.attributes('-topmost', True)
        
        lbl = tk.Label(self.overlay, text="SISTEM KILITLI", bg="black", fg="#FF003C", font=("Consolas", 48, "bold"))
        lbl.pack(expand=True)
        
        btn = tk.Button(self.overlay, text="KILIDI AC", bg="#FF003C", fg="white", font=("Consolas", 14), command=self.unlock)
        btn.pack(pady=50)

    def unlock(self):
        pwd = simpledialog.askstring("Guvenlik", "Root sifresini girin:", show="*")
        if not pwd:
            return
            
        salt = '_RECON_SECURE_SALT_V1_'
        hashed = hashlib.sha256((pwd + salt).encode()).hexdigest()
        
        db = DatabaseEngine()
        if hasattr(db, '_R_P') and hashed == db._R_P:
            self.overlay.destroy()
            for widget in self.admin.winfo_children():
                try:
                    widget.configure(state="normal")
                except:
                    pass
        else:
            messagebox.showerror("HATA", "Hatali Sifre!")

    def cleanup(self):
        self.is_running = False
