from functools import wraps
from flask import request, jsonify
import jwt
from config import Config

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Header'dan token'ı al (Bearer <token>)
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token formatı geçersiz!'}), 401
        
        if not token:
            return jsonify({'message': 'Token bulunamadı!'}), 401
        
        try:
            # Token'ı çöz
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user_rol = data['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token süresi dolmuş!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Geçersiz token!'}), 401
            
        # Fonksiyona rolü gönder
        return f(current_user_rol, *args, **kwargs)
    
    return decorated