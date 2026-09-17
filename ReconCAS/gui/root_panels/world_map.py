import tkinter as tk
import time

class WorldMapPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        self.running = True
        self.dash_offset = 0
        self.pulse_state = 0
        
        if not hasattr(self.admin, 'nodes'):
            self.admin.nodes = {
                "PUPPET-01": {"latency": "42ms"},
                "PUPPET-02": {"latency": "115ms"},
                "PUPPET-03": {"latency": "180ms"}
            }
            
        self.build()
        self.animate()
        
    def build(self):
        self.main_frame = tk.Frame(self.parent, bg="#0d111a")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.main_frame, width=800, height=400, bg="#07080d", highlightthickness=1, highlightbackground="#202636")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.info_panel = tk.Frame(self.main_frame, bg="#111624", width=200)
        self.info_panel.pack(side="right", fill="y", padx=(10, 0))
        self.info_panel.pack_propagate(False)
        
        tk.Label(self.info_panel, text="GLOBAL NODES", bg="#111624", fg="#00E5FF", font=("Consolas", 10, "bold")).pack(pady=10)
        
        self.node_labels = {}
        for name in ["PUPPET-01", "PUPPET-02", "PUPPET-03"]:
            lbl = tk.Label(self.info_panel, text=f"{name}\nWAITING...", bg="#111624", fg="#00FF41", font=("Consolas", 9), justify="left")
            lbl.pack(anchor="w", padx=10, pady=5)
            self.node_labels[name] = lbl
            
        self.draw_map()
        self.draw_nodes()
        
    def draw_map(self):
        na = [50,50, 200,50, 250,150, 150,220, 80,180]
        sa = [180,240, 250,240, 230,350, 190,380]
        eu = [380,50, 500,50, 480,120, 360,120]
        af = [360,140, 480,140, 450,280, 380,280]
        asia = [520,30, 750,30, 700,200, 500,180]
        aus = [650,260, 750,260, 720,350, 630,320]
        
        for cont in [na, sa, eu, af, asia, aus]:
            self.canvas.create_polygon(cont, outline="#003300", fill="", width=2)
            
    def draw_nodes(self):
        self.nodes_data = {
            "PUPPET-01": {"x": 120, "y": 160, "color": "#00FF41"},
            "PUPPET-02": {"x": 430, "y": 140, "color": "#00E5FF"},
            "PUPPET-03": {"x": 680, "y": 165, "color": "#BD00FF"}
        }
        
        self.conn_lines = []
        self.conn_lines.append(self.canvas.create_line(120, 160, 430, 140, fill="#FFD700", dash=(4, 4)))
        self.conn_lines.append(self.canvas.create_line(430, 140, 680, 165, fill="#FFD700", dash=(4, 4)))
        self.conn_lines.append(self.canvas.create_line(120, 160, 680, 165, fill="#FFD700", dash=(4, 4)))
        
        self.node_ovals = {}
        for name, data in self.nodes_data.items():
            x, y = data["x"], data["y"]
            c = data["color"]
            o = self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=c, outline="")
            self.canvas.create_text(x, y-15, text=name, fill=c, font=("Consolas", 8))
            self.node_ovals[name] = o
            
    def animate(self):
        if not self.running:
            return
            
        self.dash_offset = (self.dash_offset + 1) % 8
        self.pulse_state = (self.pulse_state + 1) % 2
        
        for line in self.conn_lines:
            self.canvas.itemconfig(line, dashoffset=self.dash_offset)
            
        for name, o in self.node_ovals.items():
            x, y = self.nodes_data[name]["x"], self.nodes_data[name]["y"]
            r = 6 if self.pulse_state else 4
            self.canvas.coords(o, x-r, y-r, x+r, y+r)
            
        for name in self.nodes_data.keys():
            lat = self.admin.nodes.get(name, {}).get("latency", "N/A")
            self.node_labels[name].config(text=f"{name}\nLATENCY: {lat}")
            
        self.admin.after(500, self.animate)
        
    def cleanup(self):
        self.running = False
