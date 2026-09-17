import os
import sys
import importlib.util
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class PluginSystemPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        # Project root: gui/root_panels -> gui -> ReconCAS
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.plugins_dir = os.path.join(self.project_root, 'plugins')
        self.build()

    def build(self):
        # UI Setup
        self.parent.configure(bg="#0d111a")
        
        header_frame = tk.Frame(self.parent, bg="#0d111a")
        header_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(header_frame, text="PLUGIN SISTEMI", font=("Consolas", 14, "bold"), fg="#00E5FF", bg="#0d111a").pack(side=tk.LEFT)
        
        tk.Button(header_frame, text="[ 🔄 PLUGINLERI YENILE ]", font=("Consolas", 9, "bold"), bg="#111624", fg="#00FF41", 
                  command=self.load_plugins, relief=tk.FLAT, activebackground="#202636", activeforeground="#00FF41").pack(side=tk.RIGHT, padx=5)
                  
        tk.Button(header_frame, text="[ YENI PLUGIN SABLONU OLUSTUR ]", font=("Consolas", 9, "bold"), bg="#111624", fg="#FFD700", 
                  command=self.create_template, relief=tk.FLAT, activebackground="#202636", activeforeground="#FFD700").pack(side=tk.RIGHT, padx=5)
                  
        # Scrollable frame setup
        self.canvas = tk.Canvas(self.parent, bg="#0d111a", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview, bg="#0d111a")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#0d111a")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        self.scrollbar.pack(side="right", fill="y")
        
        self.load_plugins()
        
    def load_plugins(self):
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        if not os.path.exists(self.plugins_dir):
            try:
                os.makedirs(self.plugins_dir, exist_ok=True)
            except Exception:
                pass
            
        if not os.path.exists(self.plugins_dir):
            tk.Label(self.scrollable_frame, text="Hic plugin bulunamadi.", font=("Consolas", 10), fg="#00FF41", bg="#0d111a").pack(pady=20)
            return
            
        plugin_files = [f for f in os.listdir(self.plugins_dir) if f.endswith('.py') and f != '__init__.py']
        
        if not plugin_files:
            tk.Label(self.scrollable_frame, text="Hic plugin bulunamadi.", font=("Consolas", 10), fg="#00FF41", bg="#0d111a").pack(pady=20)
            return
            
        for p_file in plugin_files:
            self.load_single_plugin(p_file)
            
    def load_single_plugin(self, filename):
        filepath = os.path.join(self.plugins_dir, filename)
        module_name = filename[:-3]
        
        card = tk.Frame(self.scrollable_frame, bg="#111624", bd=1, relief=tk.SOLID, highlightbackground="#202636", highlightthickness=1)
        card.pack(fill=tk.X, pady=5, padx=5, expand=True)
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            p_name = getattr(module, 'PLUGIN_NAME', module_name)
            p_version = getattr(module, 'PLUGIN_VERSION', '1.0')
            p_desc = getattr(module, 'PLUGIN_DESCRIPTION', 'Aciklama yok.')
            
            # Left side: info
            info_frame = tk.Frame(card, bg="#111624")
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            tk.Label(info_frame, text=f"{p_name} v{p_version}", font=("Consolas", 10, "bold"), fg="#FFD700", bg="#111624").pack(anchor=tk.W)
            tk.Label(info_frame, text=p_desc, font=("Consolas", 9), fg="#00FF41", bg="#111624", wraplength=400, justify=tk.LEFT).pack(anchor=tk.W, pady=2)
            tk.Label(info_frame, text=f"Dosya: {filename}", font=("Consolas", 8), fg="#202636", bg="#111624").pack(anchor=tk.W)
            
            # Right side: button
            btn_frame = tk.Frame(card, bg="#111624")
            btn_frame.pack(side=tk.RIGHT, padx=10, pady=10)
            
            tk.Button(btn_frame, text="[ CALISTIR ]", font=("Consolas", 9, "bold"), bg="#0d111a", fg="#00E5FF",
                      command=lambda m=module: self.run_plugin(m), relief=tk.FLAT).pack()
                      
        except Exception as e:
            err_text = f"{filename} yuklenirken hata olustu:\n{str(e)}\n{traceback.format_exc()}"
            tk.Label(card, text=f"HATA: {filename}", font=("Consolas", 10, "bold"), fg="#FF003C", bg="#111624").pack(anchor=tk.W, padx=10, pady=(10,0))
            err_label = tk.Label(card, text=err_text, font=("Consolas", 8), fg="#FF003C", bg="#111624", justify=tk.LEFT)
            err_label.pack(anchor=tk.W, padx=10, pady=5)
            
    def run_plugin(self, module):
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Plugin Calistir: {getattr(module, 'PLUGIN_NAME', 'Plugin')}")
        dialog.configure(bg="#0d111a")
        dialog.geometry("500x400")
        
        tk.Label(dialog, text="Girdi (Input):", font=("Consolas", 9, "bold"), fg="#00FF41", bg="#0d111a").pack(anchor=tk.W, padx=10, pady=(10,2))
        entry = tk.Entry(dialog, font=("Consolas", 9), bg="#111624", fg="#00FF41", insertbackground="#00FF41")
        entry.pack(fill=tk.X, padx=10, pady=2)
        
        result_text = tk.Text(dialog, font=("Consolas", 9), bg="#111624", fg="#00FF41", height=15)
        
        def execute():
            val = entry.get()
            result_text.delete(1.0, tk.END)
            try:
                if hasattr(module, 'execute'):
                    res = module.execute(val)
                    result_text.insert(tk.END, str(res))
                else:
                    result_text.insert(tk.END, "HATA: Plugin 'execute(input_text)' fonksiyonuna sahip degil.")
            except Exception as e:
                result_text.insert(tk.END, f"HATA:\n{str(e)}\n{traceback.format_exc()}")
                
        tk.Button(dialog, text="[ CALISTIR ]", font=("Consolas", 9, "bold"), bg="#111624", fg="#00E5FF", command=execute, relief=tk.FLAT).pack(pady=10)
        
        tk.Label(dialog, text="Cikti (Output):", font=("Consolas", 9, "bold"), fg="#00FF41", bg="#0d111a").pack(anchor=tk.W, padx=10)
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2,10))
        
    def create_template(self):
        if not os.path.exists(self.plugins_dir):
            try:
                os.makedirs(self.plugins_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Hata", f"Plugin dizini olusturulamadi: {e}")
                return
            
        template = 'PLUGIN_NAME = "Yeni Plugin"\nPLUGIN_VERSION = "1.0"\nPLUGIN_DESCRIPTION = "Bu bir ornek plugindir."\n\ndef execute(input_text):\n    return f"Girdi alindi: {input_text}"\n'
        
        filename = simpledialog.askstring("Yeni Plugin", "Plugin dosya adi (ornek: my_plugin):")
        if not filename: return
        if not filename.endswith('.py'): filename += '.py'
        
        filepath = os.path.join(self.plugins_dir, filename)
        if os.path.exists(filepath):
            messagebox.showerror("Hata", "Dosya zaten mevcut!")
            return
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
            
        messagebox.showinfo("Basarili", f"Plugin sablonu olusturuldu: {filename}")
        self.load_plugins()
