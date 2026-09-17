import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class SteganographyPanel:
    def __init__(self, parent_frame, admin_window):
        self.parent = parent_frame
        self.admin = admin_window
        self.encode_image_path = None
        self.decode_image_path = None
        self.build()
        
    def build(self):
        self.main_frame = tk.Frame(self.parent, bg="#0d111a")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # SECTION 1: ENCODE
        enc_frame = tk.LabelFrame(self.main_frame, text=" MESAJ GIZLEME (ENCODE) ", bg="#111624", fg="#00FF41", font=("Consolas", 10, "bold"))
        enc_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        btn_sel_enc = tk.Button(enc_frame, text="[ GORSEL SEC ]", bg="#202636", fg="#00E5FF", command=self.select_encode_image)
        btn_sel_enc.pack(pady=10)
        
        self.lbl_enc_info = tk.Label(enc_frame, text="Secilen: Yok", bg="#111624", fg="#FFD700", font=("Consolas", 9))
        self.lbl_enc_info.pack()
        
        tk.Label(enc_frame, text="Gizlenecek Mesaj:", bg="#111624", fg="#00FF41", font=("Consolas", 9)).pack(pady=(10,0))
        self.txt_encode = tk.Text(enc_frame, height=5, width=40, bg="#0d111a", fg="#00FF41", insertbackground="#00FF41")
        self.txt_encode.pack(pady=5)
        
        btn_enc = tk.Button(enc_frame, text="[ GIZLE VE KAYDET ]", bg="#202636", fg="#BD00FF", command=self.encode_message)
        btn_enc.pack(pady=10)
        
        # SECTION 2: DECODE
        dec_frame = tk.LabelFrame(self.main_frame, text=" MESAJ CIKARMA (DECODE) ", bg="#111624", fg="#00FF41", font=("Consolas", 10, "bold"))
        dec_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        btn_sel_dec = tk.Button(dec_frame, text="[ STEGANOGRAFILI GORSEL SEC ]", bg="#202636", fg="#00E5FF", command=self.select_decode_image)
        btn_sel_dec.pack(pady=10)
        
        self.lbl_dec_info = tk.Label(dec_frame, text="Secilen: Yok", bg="#111624", fg="#FFD700", font=("Consolas", 9))
        self.lbl_dec_info.pack()
        
        btn_dec = tk.Button(dec_frame, text="[ MESAJI CIKAR ]", bg="#202636", fg="#BD00FF", command=self.decode_message)
        btn_dec.pack(pady=10)
        
        tk.Label(dec_frame, text="Cikarilan Mesaj:", bg="#111624", fg="#00FF41", font=("Consolas", 9)).pack(pady=(10,0))
        self.txt_decode = tk.Text(dec_frame, height=5, width=40, bg="#0d111a", fg="#00E5FF")
        self.txt_decode.pack(pady=5)
        
        # SECTION 3: INFO
        info_frame = tk.LabelFrame(self.main_frame, text=" BILGI ", bg="#111624", fg="#00FF41", font=("Consolas", 10, "bold"))
        info_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        info_text = "LSB (Least Significant Bit) Steganografisi, gorseldeki piksellerin en onemsiz bitlerini degistirerek\n" \
                    "veri gizler. Gorselde gozle gorulur bir degisiklik yaratmaz.\n" \
                    "Kapasite: Piksellerin renk kanallarinin sayisina baglidir."
        tk.Label(info_frame, text=info_text, bg="#111624", fg="#00FF41", font=("Consolas", 9), justify="left").pack(pady=10)
        
        self.lbl_capacity = tk.Label(info_frame, text="Maksimum Kapasite: 0 karakter", bg="#111624", fg="#FFD700", font=("Consolas", 9))
        self.lbl_capacity.pack(pady=5)

    def select_encode_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.bmp")])
        if path:
            self.encode_image_path = path
            img = Image.open(path)
            w, h = img.size
            cap = (w * h * 3) // 8 - 4
            self.lbl_enc_info.config(text=f"{os.path.basename(path)} ({w}x{h})")
            self.lbl_capacity.config(text=f"Maksimum Kapasite: {cap} karakter")
            
    def encode_message(self):
        if not self.encode_image_path:
            messagebox.showerror("Hata", "Gorsel secin.")
            return
        msg = self.txt_encode.get("1.0", tk.END).strip()
        if not msg:
            messagebox.showerror("Hata", "Mesaj girin.")
            return
            
        img = Image.open(self.encode_image_path)
        img = img.convert("RGB")
        w, h = img.size
        max_bytes = (w * h * 3) // 8 - 4
        
        msg_bytes = msg.encode('utf-8')
        if len(msg_bytes) > max_bytes:
            messagebox.showerror("Hata", "Mesaj cok uzun.")
            return
            
        out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not out_path:
            return
            
        pixels = list(img.getdata())
        msg_len = len(msg_bytes)
        bin_len = format(msg_len, '032b')
        bin_msg = ''.join([format(b, '08b') for b in msg_bytes])
        full_bin = bin_len + bin_msg
        
        new_pixels = []
        idx = 0
        for p in pixels:
            r, g, b = p
            if idx < len(full_bin):
                r = (r & ~1) | int(full_bin[idx])
                idx += 1
            if idx < len(full_bin):
                g = (g & ~1) | int(full_bin[idx])
                idx += 1
            if idx < len(full_bin):
                b = (b & ~1) | int(full_bin[idx])
                idx += 1
            new_pixels.append((r,g,b))
            
        new_img = Image.new("RGB", img.size)
        new_img.putdata(new_pixels)
        new_img.save(out_path)
        messagebox.showinfo("Basarili", f"Mesaj gizlendi! ({msg_len} bayt)")
        
    def select_decode_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
        if path:
            self.decode_image_path = path
            self.lbl_dec_info.config(text=f"{os.path.basename(path)}")
            
    def decode_message(self):
        if not self.decode_image_path:
            messagebox.showerror("Hata", "Gorsel secin.")
            return
            
        img = Image.open(self.decode_image_path)
        img = img.convert("RGB")
        pixels = list(img.getdata())
        
        bits = []
        for p in pixels:
            bits.append(str(p[0] & 1))
            bits.append(str(p[1] & 1))
            bits.append(str(p[2] & 1))
            
        if len(bits) < 32:
            return
            
        len_str = ''.join(bits[:32])
        msg_len = int(len_str, 2)
        
        if msg_len * 8 > len(bits) - 32 or msg_len < 0:
            messagebox.showerror("Hata", "Gecerli bir mesaj bulunamadi.")
            return
            
        msg_bits = bits[32:32 + msg_len * 8]
        msg_bytes = bytearray()
        for i in range(0, len(msg_bits), 8):
            byte_val = int(''.join(msg_bits[i:i+8]), 2)
            msg_bytes.append(byte_val)
            
        try:
            decoded = msg_bytes.decode('utf-8')
            self.txt_decode.delete("1.0", tk.END)
            self.txt_decode.insert("1.0", decoded)
        except Exception as e:
            messagebox.showerror("Hata", "Mesaj cozulurken hata olustu.")
