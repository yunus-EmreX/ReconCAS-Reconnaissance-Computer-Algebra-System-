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

if __name__ == '__main__':
    unittest.main()
