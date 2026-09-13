import tkinter as tk
from tkinter import messagebox
from core.auth_engine import DatabaseEngine, AuthError
from gui.theme import THEME

class AuthGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SYSTEM.LOGIN // V0.1 PRE-RELEASE")
        self.geometry("380x440")
        self.resizable(False, False)
        self.configure(bg=THEME["bg"])
        self.current_user_id = None
        
        try:
            DatabaseEngine.init_db()
        except AuthError as e:
            messagebox.showerror("CRITICAL_DB_ERROR", str(e))
            self.destroy()
            
        self.build_ui()
        
    def build_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        tk.Label(self, text="=== TERMINAL AUTH ===", font=("Consolas", 16, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self, text=">_ USERNAME:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.ent_user = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.ent_user.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ PASSWORD:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.ent_pass = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], show="*")
        self.ent_pass.pack(fill="x", padx=40, pady=5)
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1}
        tk.Button(self, text="[ LOGIN ]", command=self.do_login, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="[ CREATE_ACCOUNT ]", command=self.show_register, **btn_st).pack(fill="x", padx=40, pady=5)
        tk.Button(self, text="[ FORGOT_PASSWORD ]", command=self.show_reset, fg=THEME["accent"], bg=THEME["btn_bg"], font=THEME["font_main"], relief="flat", bd=0).pack(pady=10)

    def do_login(self):
        username = self.ent_user.get()
        success, res = DatabaseEngine.login(username, self.ent_pass.get())
        if success:
            self.current_user_id = res
            DatabaseEngine.log_session_activity(self.current_user_id, "SYSTEM_AUTH", "LOGIN_SUCCESS")
            self.destroy()
        else: 
            messagebox.showerror("AUTH_FAILED", res)

    def show_register(self):
        for widget in self.winfo_children(): widget.destroy()
        tk.Label(self, text="=== NEW OPERATIVE ===", font=("Consolas", 16, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self, text=">_ SET USERNAME:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_user = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.reg_user.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ SET PASSWORD:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_pass = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], show="*")
        self.reg_pass.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ SECRET HINT (For Reset):", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.reg_hint = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.reg_hint.pack(fill="x", padx=40, pady=5)
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1}
        tk.Button(self, text="[ REGISTER_PROTOCOL ]", command=self.do_register, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="<< BACK", command=self.build_ui, bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack()

    def do_register(self):
        try:
            success, msg = DatabaseEngine.register(self.reg_user.get(), self.reg_pass.get(), self.reg_hint.get())
            messagebox.showinfo("SYS_MSG", msg)
            if success: self.build_ui()
        except AuthError as e: messagebox.showerror("AUTH_ERROR", str(e))

    def show_reset(self):
        for widget in self.winfo_children(): widget.destroy()
        tk.Label(self, text="=== PASSWORD OVERRIDE ===", font=("Consolas", 16, "bold"), fg=THEME["accent"], bg=THEME["bg"]).pack(pady=20)
        
        tk.Label(self, text=">_ USERNAME:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.res_user = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.res_user.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ SECRET HINT:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.res_hint = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"])
        self.res_hint.pack(fill="x", padx=40, pady=5)
        
        tk.Label(self, text=">_ NEW PASSWORD:", font=THEME["font_main"], fg=THEME["fg"], bg=THEME["bg"]).pack(anchor="w", padx=40)
        self.res_pass = tk.Entry(self, font=("Consolas", 12), bg=THEME["btn_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], show="*")
        self.res_pass.pack(fill="x", padx=40, pady=5)
        
        btn_st = {"font": THEME["font_main"], "bg": THEME["btn_bg"], "fg": THEME["fg"], "activebackground": THEME["active"], "relief": "flat", "bd": 1}
        tk.Button(self, text="[ OVERRIDE_PROTOCOL ]", command=self.do_reset, **btn_st).pack(fill="x", padx=40, pady=15)
        tk.Button(self, text="<< BACK", command=self.build_ui, bg=THEME["bg"], fg=THEME["accent"], relief="flat").pack()

    def do_reset(self):
        success, msg = DatabaseEngine.reset_password(self.res_user.get(), self.res_hint.get(), self.res_pass.get())
        if success:
            messagebox.showinfo("SYS_MSG", msg)
            self.build_ui()
        else:
            messagebox.showerror("AUTH_ERROR", msg)

