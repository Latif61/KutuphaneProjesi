from flask import Blueprint, request, jsonify
from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.utils.decorators import token_required
import jwt
from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

auth_service = AuthService()
repo = UserRepository()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    res = auth_service.register_user(data.get('ad'), data.get('soyad'), data.get('email'), data.get('sifre'), data.get('rol_id', 3))
    return jsonify(res), 201 if res['success'] else 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    res = auth_service.login_user(data.get('email'), data.get('sifre'))
    return jsonify(res), 200 if res['success'] else 401

# --- YENİ: KENDİ BİLGİLERİNİ GETİR ---
@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user_rol):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = data['user_id']
        
        user = repo.find_by_id(user_id)
        if user:
            del user['sifre'] # Güvenlik için şifreyi gizle
            return jsonify({"success": True, "data": user})
        return jsonify({"success": False, "message": "Kullanıcı bulunamadı."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# --- YENİ: PROFİL GÜNCELLE ---
@auth_bp.route('/update-profile', methods=['POST'])
@token_required
def update_profile(current_user_rol):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        user_data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = user_data['user_id']
        
        data = request.get_json()
        password = data.get('sifre') if data.get('sifre') and len(data.get('sifre')) > 0 else None
        
        success = repo.update_profile(user_id, data.get('ad'), data.get('soyad'), data.get('email'), data.get('avatar'), password)
        
        if success:
            return jsonify({"success": True, "message": "Profil güncellendi!"})
        return jsonify({"success": False, "message": "Güncelleme başarısız."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@auth_bp.route('/list', methods=['GET'])
@token_required
def get_users(current_user_rol):
    if current_user_rol == 3: return jsonify({"success": False, "message": "Yetkisiz işlem!"}), 403
    users = repo.get_all_users()
    return jsonify({"success": True, "data": users})

@auth_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user_rol, user_id):
    if current_user_rol != 1: return jsonify({"success": False, "message": "Sadece Yöneticiler!"}), 403
    result = repo.delete_user(user_id)
    if result: return jsonify({"success": True, "message": "Üye silindi."})
    else: return jsonify({"success": False, "message": "Silinemedi."})

