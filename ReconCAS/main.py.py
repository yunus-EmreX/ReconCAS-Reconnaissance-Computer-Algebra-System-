from gui.app_windows import AuthGUI

if __name__ == '__main__':
    auth = AuthGUI()
    auth.mainloop()
    
    # Giriş başarılı olursa Terminali Başlat
    if hasattr(auth, 'current_user_id') and auth.current_user_id:
        from gui.app_windows import TerminalGUI
        app = TerminalGUI(user_id=auth.current_user_id)
        app.mainloop()