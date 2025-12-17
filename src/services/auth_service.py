import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from src.repositories.user_repository import UserRepository
from config import Config

class AuthService:
    def __init__(self):
        self.repo = UserRepository()

    def register_user(self, ad, soyad, email, sifre, rol_id):
        hashed_password = generate_password_hash(sifre)
        if self.repo.create_user(ad, soyad, email, hashed_password, rol_id):
            return {"success": True, "message": "Kayıt başarılı"}
        return {"success": False, "message": "Kayıt başarısız"}

    def login_user(self, email, sifre):
        user = self.repo.find_by_email(email)
        if user:
            db_password = str(user['sifre'])
            input_password = str(sifre)
            is_valid = False
            
            if db_password == input_password: is_valid = True
            else:
                try:
                    if check_password_hash(db_password, input_password): is_valid = True
                except: pass

            if is_valid:
                token = jwt.encode({
                    'user_id': user['id'],
                    'rol_id': user['rol_id'], # Düzeltildi
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, Config.SECRET_KEY, algorithm="HS256")
                return {"success": True, "token": token, "role": user['rol_id'], "user": f"{user['ad']} {user['soyad']}"}
        
        return {"success": False, "message": "Hatalı Giriş"}