import tkinter as tk
from gui.theme import THEME

class AnimatedToggle(tk.Canvas):
    """Sağa kayarak açılan Siberpunk Toggle Butonu"""
    def __init__(self, parent, command=None):
        super().__init__(parent, width=50, height=24, bg=THEME["bg"], highlightthickness=0)
        self.state = False
        self.command = command
        
        # Arka plan hapı
        self.bg_id = self.create_oval(2, 2, 22, 22, fill=THEME["btn_bg"], outline=THEME["grid"])
        self.bg_id2 = self.create_oval(28, 2, 48, 22, fill=THEME["btn_bg"], outline=THEME["grid"])
        self.bg_rect = self.create_rectangle(12, 2, 38, 22, fill=THEME["btn_bg"], outline=THEME["btn_bg"])
        
        # Hareketli daire (Switch)
        self.circle_id = self.create_oval(4, 4, 20, 20, fill="#555555", outline="#555555")
        self.bind("<Button-1>", self.toggle)
        
    def toggle(self, event=None):
        self.state = not self.state
        if self.state:
            self.itemconfig(self.bg_id, fill=THEME["active"], outline=THEME["active"])
            self.itemconfig(self.bg_id2, fill=THEME["active"], outline=THEME["active"])
            self.itemconfig(self.bg_rect, fill=THEME["active"], outline=THEME["active"])
            self.itemconfig(self.circle_id, fill="#000000")
            self.coords(self.circle_id, 30, 4, 46, 20) 
        else:
            self.itemconfig(self.bg_id, fill=THEME["btn_bg"], outline=THEME["grid"])
            self.itemconfig(self.bg_id2, fill=THEME["btn_bg"], outline=THEME["grid"])
            self.itemconfig(self.bg_rect, fill=THEME["btn_bg"], outline=THEME["btn_bg"])
            self.itemconfig(self.circle_id, fill="#555555")
            self.coords(self.circle_id, 4, 4, 20, 20) 
            
        if self.command:
            self.command(self.state)

