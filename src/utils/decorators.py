from functools import wraps
from flask import request, jsonify
import jwt
from config import Config

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 1. Header'da Token var mı?
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1] # "Bearer <token>" kısmından token'ı al

        if not token:
            return jsonify({'message': 'Token eksik! Lütfen giriş yapın.'}), 401

        try:
            # 2. Token'ı çöz (Decode)
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            
            # --- HATAYI ÇÖZEN KISIM BURASI ---
            # Eskiden data['role_id'] yazıyordu, şimdi data['rol_id'] yaptık.
            current_user_rol = data['rol_id'] 
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Oturum süresi doldu. Tekrar giriş yapın.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Geçersiz Token!'}), 401
        except KeyError:
             return jsonify({'message': 'Token formatı hatalı (Rol bulunamadı)!'}), 401

        # 3. Fonksiyonu çalıştır ve rolü gönder
        return f(current_user_rol, *args, **kwargs)

    return decorated