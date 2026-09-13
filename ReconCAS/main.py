import sys
import traceback

# Windows High-DPI Awareness (BUG-DPI: %125/%150 ekran ölçeklemesinde koordinat kaymasını önler)
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

print(">_ SİSTEM BAŞLATILIYOR...")

try:
    from gui.app_windows import AuthGUI

    if __name__ == '__main__':
        auth = AuthGUI()
        auth.mainloop()
        
        # Giriş başarılı olursa Terminali Başlat
        if hasattr(auth, 'current_user_id') and auth.current_user_id:
            from gui.app_windows import TerminalGUI
            app = TerminalGUI(user_id=auth.current_user_id)
            app.mainloop()

except Exception as e:
    print("\n[!] FATAL ERROR - SİSTEM ÇÖKTÜ [!]")
    print("=" * 50)
    traceback.print_exc()  # Bu kod hatanın hangi dosya ve satırda olduğunu gösterecek
    print("=" * 50)
    input("\nHata detaylarını okuduktan sonra pencereyi kapatmak için ENTER'a basın...")