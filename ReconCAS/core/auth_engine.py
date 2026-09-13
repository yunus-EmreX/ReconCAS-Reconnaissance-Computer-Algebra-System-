import sqlite3
import bcrypt
import os
from datetime import datetime

# --- ÖZEL HATA SINIFLARI ---
class AuthError(Exception):
    """Veritabanı ve Kimlik Doğrulama Hataları için özel sınıf"""
    pass

class DatabaseEngine:
    # Veritabanını her zaman ReconCAS ana dizinine kur
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_NAME = os.path.join(BASE_DIR, "recon_cas_secure.db")

    @staticmethod
    def init_db():
        try:
            conn = sqlite3.connect(DatabaseEngine.DB_NAME)
            c = conn.cursor()
            # OWASP standardı: Parola ve Hint (ipucu) hash (BLOB) olarak saklanır
            c.execute('''CREATE TABLE IF NOT EXISTS users 
                         (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash BLOB, hint_hash BLOB)''')
            c.execute('''CREATE TABLE IF NOT EXISTS history 
                         (id INTEGER PRIMARY KEY, user_id INTEGER, equation TEXT, result TEXT, timestamp TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e:
            raise AuthError(f"Veritabanı başlatılamadı: {e}")

    @staticmethod
    def _hash_data(data: str) -> bytes:
        """Veriyi 'Salt' ekleyerek bcrypt ile güçlü şekilde şifreler"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(data.encode('utf-8'), salt)

    @staticmethod
    def _verify_data(data: str, hashed_data: bytes) -> bool:
        """Girilen metnin şifresiyle uyuşup uyuşmadığını kontrol eder"""
        return bcrypt.checkpw(data.encode('utf-8'), hashed_data)

    @staticmethod
    def register(username, password, hint):
        try:
            conn = sqlite3.connect(DatabaseEngine.DB_NAME)
            c = conn.cursor()
            
            pass_hash = DatabaseEngine._hash_data(password)
            hint_hash = DatabaseEngine._hash_data(hint.lower().strip()) # İpuçları küçük harfe çevrilip şifrelenir
            
            c.execute("INSERT INTO users (username, password_hash, hint_hash) VALUES (?, ?, ?)", 
                      (username, pass_hash, hint_hash))
            conn.commit()
            conn.close()
            return True, "OPERATÖR KAYDI BAŞARILI."
        except sqlite3.IntegrityError:
            return False, "BU KULLANICI ADI SİSTEMDE MEVCUT."
        except Exception as e:
            raise AuthError(f"Kayıt Hatası: {e}")

    @staticmethod
    def login(username, password):
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        
        # Kullanıcı var mı ve parola eşleşiyor mu?
        if user and DatabaseEngine._verify_data(password, user[1]):
            return True, user[0]
        return False, "KİMLİK DOĞRULAMA BAŞARISIZ."

    @staticmethod
    def reset_password(username, hint, new_password):
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, hint_hash FROM users WHERE username=?", (username,))
        user = c.fetchone()
        
        if user and DatabaseEngine._verify_data(hint.lower().strip(), user[1]):
            new_pass_hash = DatabaseEngine._hash_data(new_password)
            c.execute("UPDATE users SET password_hash=? WHERE id=?", (new_pass_hash, user[0]))
            conn.commit()
            conn.close()
            return True, "PAROLA GÜVENLİ ŞEKİLDE GÜNCELLENDİ."
            
        conn.close()
        return False, "KULLANICI ADI VEYA GİZLİ YANIT HATALI."

    @staticmethod
    def log_session_activity(user_id, equation, result):
        if not user_id: return
        try:
            conn = sqlite3.connect(DatabaseEngine.DB_NAME)
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO history (user_id, equation, result, timestamp) VALUES (?, ?, ?, ?)", 
                      (user_id, equation, result, timestamp))
            conn.commit()
            conn.close()
        except Exception as e:
            raise AuthError(f"Log Kayıt Hatası: {e}")

    @staticmethod
    def get_history(user_id):
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT timestamp, equation, result FROM history WHERE user_id=? ORDER BY id DESC LIMIT 50", (user_id,))
        records = c.fetchall()
        conn.close()
        return records