import sys
import traceback

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