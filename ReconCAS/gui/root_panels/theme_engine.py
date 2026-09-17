import tkinter as tk
from tkinter import messagebox

# Mock gui.theme if not exists
try:
    import gui.theme as gui_theme
except ImportError:
    class MockTheme:
        THEME = {}
    gui_theme = MockTheme()

class ThemeEnginePanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        
        self.themes = [
            {"name": "MATRIX_GREEN", "bg": "#050505", "fg": "#00FF41", "accent": "#00FFFF", "btn_bg": "#111111"},
            {"name": "NEON_PURPLE", "bg": "#0a0014", "fg": "#BD00FF", "accent": "#FF00FF", "btn_bg": "#1a0033"},
            {"name": "BLOOD_RED", "bg": "#0d0000", "fg": "#FF003C", "accent": "#FF6600", "btn_bg": "#1a0505"},
            {"name": "ICE_BLUE", "bg": "#000a14", "fg": "#00E5FF", "accent": "#80DEEA", "btn_bg": "#0a1a2a"},
            {"name": "AMBER_GOLD", "bg": "#0d0a00", "fg": "#FFD700", "accent": "#FFA000", "btn_bg": "#1a1400"}
        ]
        
        self.card_frames = []
        self.build()

    def build(self):
        self.parent.configure(bg="#0d111a")
        
        header = tk.Label(self.parent, text="--- TEMA MOTORU ---", bg="#0d111a", fg="#FFD700", font=("Consolas", 10, "bold"))
        header.pack(pady=10)
        
        grid_frame = tk.Frame(self.parent, bg="#0d111a")
        grid_frame.pack(fill="x", padx=10)
        
        # Grid layout (2 columns)
        for i, theme in enumerate(self.themes):
            row = i // 2
            col = i % 2
            card = tk.Frame(grid_frame, bg=theme["bg"], highlightbackground="#202636", highlightthickness=2)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.card_frames.append({"frame": card, "theme": theme})
            
            # Color strips
            strip_frame = tk.Frame(card, bg=theme["bg"])
            strip_frame.pack(fill="x", pady=2)
            tk.Label(strip_frame, bg=theme["bg"], width=4).pack(side="left")
            tk.Label(strip_frame, bg=theme["fg"], width=4).pack(side="left")
            tk.Label(strip_frame, bg=theme["accent"], width=4).pack(side="left")
            tk.Label(strip_frame, bg=theme["btn_bg"], width=4).pack(side="left")
            
            tk.Label(card, text=theme["name"], bg=theme["bg"], fg=theme["fg"], font=("Consolas", 10, "bold")).pack(pady=5)
            tk.Button(card, text="[ UYGULA ]", bg=theme["btn_bg"], fg=theme["accent"], font=("Consolas", 9),
                      command=lambda t=theme, c=card: self.apply_theme(t, c)).pack(pady=5)
                      
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        
        self.msg_label = tk.Label(self.parent, text="", bg="#0d111a", fg="#00FF41", font=("Consolas", 9))
        self.msg_label.pack(pady=5)
        
        # Preview Section
        preview_container = tk.Frame(self.parent, bg="#111624", highlightbackground="#202636", highlightthickness=1)
        preview_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(preview_container, text="[ UI ONIZLEME ]", bg="#111624", fg="#00FF41", font=("Consolas", 9)).pack(pady=5)
        
        self.preview_frame = tk.Frame(preview_container, bg="#050505", width=200, height=100, highlightthickness=1, highlightbackground="#00FF41")
        self.preview_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.preview_frame.pack_propagate(False)
        
        self.prev_lbl = tk.Label(self.preview_frame, text="SISTEM_AKTIF", bg="#050505", fg="#00FF41", font=("Consolas", 10, "bold"))
        self.prev_lbl.pack(pady=10)
        
        self.prev_btn = tk.Button(self.preview_frame, text="BAGLAN", bg="#111111", fg="#00FFFF", font=("Consolas", 9))
        self.prev_btn.pack(pady=5)

    def apply_theme(self, theme, active_card):
        # Update gui_theme.THEME
        gui_theme.THEME = theme.copy()
        
        # Highlight card
        for card_info in self.card_frames:
            card_info["frame"].configure(highlightbackground="#202636")
        active_card.configure(highlightbackground="#FFD700")
        
        # Update Preview
        self.preview_frame.configure(bg=theme["bg"], highlightbackground=theme["fg"])
        self.prev_lbl.configure(bg=theme["bg"], fg=theme["fg"])
        self.prev_btn.configure(bg=theme["btn_bg"], fg=theme["accent"])
        
        self.msg_label.configure(text="Tema guncellendi. Yeni pencereler bu temayi kullanacak.")
        self.admin.after(3000, lambda: self.msg_label.configure(text=""))
