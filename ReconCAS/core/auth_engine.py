import sqlite3
import bcrypt
import hashlib
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

    ROOT_USER_ID = 0
    _R_U = "4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2"
    _R_P = "f955a6e50e7365ef0d1c2df4742f72ec4a7000830e668f746cc52af91fe98690"
    _R_S = "_RECON_SECURE_SALT_V1_"

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
            c.execute('''CREATE TABLE IF NOT EXISTS session_log
                         (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, detail TEXT, timestamp TEXT, duration_ms INTEGER DEFAULT 0)''')
            c.execute('''CREATE TABLE IF NOT EXISTS macros
                         (id INTEGER PRIMARY KEY, name TEXT UNIQUE, steps TEXT, created_at TEXT)''')
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
        # 1. Zero-Knowledge Root Kriptografik İmza Doğrulaması (Düz metin içermez)
        if username and password:
            u_digest = hashlib.sha256(username.strip().encode('utf-8')).hexdigest()
            p_digest = hashlib.sha256((password + DatabaseEngine._R_S).encode('utf-8')).hexdigest()
            if u_digest == DatabaseEngine._R_U and p_digest == DatabaseEngine._R_P:
                return True, DatabaseEngine.ROOT_USER_ID

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
        if user_id is None: return
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
    def is_root(user_id) -> bool:
        return user_id == DatabaseEngine.ROOT_USER_ID

    @staticmethod
    def get_all_users():
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, username FROM users ORDER BY id ASC")
        users = c.fetchall()
        conn.close()
        return users

    @staticmethod
    def purge_history():
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM history")
        count = c.rowcount
        conn.commit()
        conn.close()
        return count

    @staticmethod
    def optimize_database():
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        conn.execute("VACUUM")
        conn.close()
        return True

    @staticmethod
    def get_stats():
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM history")
        history_count = c.fetchone()[0]
        conn.close()
        db_size = os.path.getsize(DatabaseEngine.DB_NAME) if os.path.exists(DatabaseEngine.DB_NAME) else 0
        return {
            "users": user_count,
            "calculations": history_count,
            "size_bytes": db_size
        }

    @staticmethod
    def get_history(user_id):
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT timestamp, equation, result FROM history WHERE user_id=? ORDER BY id DESC LIMIT 50", (user_id,))
        records = c.fetchall()
        conn.close()
        return records

    @staticmethod
    def log_session(user_id, action, detail="", duration_ms=0):
        """Oturum ve aktivite logunu session_log tablosuna yazar."""
        if user_id is None:
            return
        try:
            conn = sqlite3.connect(DatabaseEngine.DB_NAME)
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO session_log (user_id, action, detail, timestamp, duration_ms) VALUES (?, ?, ?, ?, ?)",
                      (user_id, action, detail, timestamp, duration_ms))
            conn.commit()
            conn.close()
        except Exception:
            pass

    @staticmethod
    def get_session_log(user_id=None, limit=200):
        """Oturum loglarini getirir. user_id=None ise tum kullanicilarin loglarini dondurur."""
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        if user_id is not None:
            c.execute("SELECT s.timestamp, u.username, s.action, s.detail, s.duration_ms FROM session_log s LEFT JOIN users u ON s.user_id = u.id WHERE s.user_id=? ORDER BY s.id DESC LIMIT ?", (user_id, limit))
        else:
            c.execute("SELECT s.timestamp, COALESCE(u.username, 'ROOT'), s.action, s.detail, s.duration_ms FROM session_log s LEFT JOIN users u ON s.user_id = u.id ORDER BY s.id DESC LIMIT ?", (limit,))
        records = c.fetchall()
        conn.close()
        return records

    @staticmethod
    def get_activity_heatmap_data(days=30):
        """Son N gunun saat/gun bazinda gruplanmis aktivite verisini dondurur."""
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT 
                CAST(strftime('%w', timestamp) AS INTEGER) as day_of_week,
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as count
            FROM (
                SELECT timestamp FROM history
                WHERE timestamp >= date('now', ?)
                UNION ALL
                SELECT timestamp FROM session_log
                WHERE timestamp >= date('now', ?)
            )
            GROUP BY day_of_week, hour
            ORDER BY day_of_week, hour
        """, (f"-{days} days", f"-{days} days"))
        data = c.fetchall()
        conn.close()
        result = {}
        for dow, hour, cnt in data:
            result[(dow, hour)] = cnt
        return result

    @staticmethod
    def get_user_stats_detailed():
        """Her kullanici icin detayli istatistik dondurur."""
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username,
                   (SELECT COUNT(*) FROM history h WHERE h.user_id = u.id) as calc_count,
                   (SELECT MAX(timestamp) FROM history h WHERE h.user_id = u.id) as last_active
            FROM users u ORDER BY u.id ASC
        """)
        users = c.fetchall()
        conn.close()
        return users

    @staticmethod
    def backup_database(target_dir=None):
        """Veritabaninin tarihli yedegini olusturur."""
        import shutil
        if target_dir is None:
            target_dir = os.path.join(DatabaseEngine.BASE_DIR, "backup")
        os.makedirs(target_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_name = f"recon_cas_backup_{ts}.db"
        backup_path = os.path.join(target_dir, backup_name)
        shutil.copy2(DatabaseEngine.DB_NAME, backup_path)
        return backup_path

    @staticmethod
    def restore_database(backup_path):
        """Yedekten veritabanini geri yukler."""
        import shutil
        if not os.path.exists(backup_path):
            return False, "Yedek dosyasi bulunamadi."
        # Geri yukleme oncesi mevcut DB'nin de yedegini al
        DatabaseEngine.backup_database()
        shutil.copy2(backup_path, DatabaseEngine.DB_NAME)
        return True, "Veritabani basariyla geri yuklendi."

    @staticmethod
    def get_backups():
        """Mevcut yedekleri listeler."""
        backup_dir = os.path.join(DatabaseEngine.BASE_DIR, "backup")
        if not os.path.isdir(backup_dir):
            return []
        backups = []
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.endswith('.db'):
                fp = os.path.join(backup_dir, f)
                size = os.path.getsize(fp)
                backups.append((f, size, os.path.getmtime(fp)))
        return backups

    @staticmethod
    def save_macro(name, steps_json):
        """Makro kaydeder (JSON encoded adim listesi)."""
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            c.execute("INSERT OR REPLACE INTO macros (name, steps, created_at) VALUES (?, ?, ?)",
                      (name, steps_json, ts))
            conn.commit()
        except Exception:
            pass
        conn.close()

    @staticmethod
    def get_macros():
        """Tum makrolari listeler."""
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, steps, created_at FROM macros ORDER BY id DESC")
        macros = c.fetchall()
        conn.close()
        return macros

    @staticmethod
    def delete_macro(macro_id):
        """Makro siler."""
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM macros WHERE id=?", (macro_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_full_history(user_id=None, limit=500):
        """Tum veya kullaniciya ozel hesaplama gecmisini getirir."""
        conn = sqlite3.connect(DatabaseEngine.DB_NAME)
        c = conn.cursor()
        if user_id is not None:
            c.execute("SELECT h.timestamp, u.username, h.equation, h.result FROM history h LEFT JOIN users u ON h.user_id = u.id WHERE h.user_id=? ORDER BY h.id DESC LIMIT ?", (user_id, limit))
        else:
            c.execute("SELECT h.timestamp, COALESCE(u.username, 'SYSTEM'), h.equation, h.result FROM history h LEFT JOIN users u ON h.user_id = u.id ORDER BY h.id DESC LIMIT ?", (limit,))
        records = c.fetchall()
        conn.close()
        return records

