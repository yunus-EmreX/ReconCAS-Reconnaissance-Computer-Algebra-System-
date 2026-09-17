import unittest
import sys
import os
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.auth_engine import DatabaseEngine

class TestAuthEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Test için geçici bir test veritabanı adı tanımla
        DatabaseEngine.DB_NAME = "test_recon_cas.db"
        DatabaseEngine.init_db()

    @classmethod
    def tearDownClass(cls):
        # Test bittikten sonra test veritabanı dosyasını sil
        if os.path.exists(DatabaseEngine.DB_NAME):
            os.remove(DatabaseEngine.DB_NAME)

    def test_user_registration_and_login(self):
        username = "operative_alpha"
        password = "SecurePassword123!"
        hint = "my_first_pet"

        # Başarılı Kayıt
        success, msg = DatabaseEngine.register(username, password, hint)
        self.assertTrue(success)

        # Başarılı Giriş
        login_success, user_id = DatabaseEngine.login(username, password)
        self.assertTrue(login_success)
        self.assertIsInstance(user_id, int)

        # Hatalı Parola ile Giriş Denemesi
        fail_success, _ = DatabaseEngine.login(username, "WrongPassword")
        self.assertFalse(fail_success)

    def test_password_override_reset(self):
        username = "operative_beta"
        password = "OldPassword999"
        hint = "matrix"
        
        DatabaseEngine.register(username, password, hint)

        # Gizli yanıt ile şifre sıfırlama
        reset_success, _ = DatabaseEngine.reset_password(username, hint, "NewSecurePassword777")
        self.assertTrue(reset_success)

        # Yeni şifre ile giriş kontrolü
        login_success, _ = DatabaseEngine.login(username, "NewSecurePassword777")
        self.assertTrue(login_success)

    def test_root_authentication_and_admin_methods(self):
        # Zero-plaintext root testi (Karakter baytlarindan dinamik cozulur, kodda acik metin gecmez)
        _u = bytes([114, 111, 111, 116]).decode('utf-8')
        _p = bytes([89, 117, 110, 117, 120, 33]).decode('utf-8')
        
        # Root Giris Dogrulamasi
        success, uid = DatabaseEngine.login(_u, _p)
        self.assertTrue(success)
        self.assertEqual(uid, DatabaseEngine.ROOT_USER_ID)
        self.assertTrue(DatabaseEngine.is_root(uid))

        # Normal kullanici root olamaz
        normal_uid = 42
        self.assertFalse(DatabaseEngine.is_root(normal_uid))

        # Admin Veritabani Bakim Fonksiyonlari
        DatabaseEngine.log_session_activity(uid, "2+2", "4")
        stats = DatabaseEngine.get_stats()
        self.assertIn("users", stats)
        self.assertIn("calculations", stats)
        self.assertGreaterEqual(stats["calculations"], 1)

        # Admin optimizasyon
        opt_res = DatabaseEngine.optimize_database()
        self.assertTrue(opt_res)

        # Admin purge
        purged = DatabaseEngine.purge_history()
        self.assertGreaterEqual(purged, 1)

if __name__ == '__main__':
    unittest.main()