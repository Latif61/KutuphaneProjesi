from flask import Blueprint, request, jsonify
from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.utils.decorators import token_required
import jwt
from config import Config

# Blueprint'i tanımlıyoruz (URL'lerin önüne /auth gelecek)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

auth_service = AuthService()
repo = UserRepository()

# bu fonksiyon gonderilen ad,soyad,email,sifre bilgilerini alir 
# ve bu bilgileri isleyerek veritabanina yeni bir kullanici olusturlmasini saglar
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() # aldigi bilgileri json formatina cevirir
    res = auth_service.register_user(
        data.get('ad'), 
        data.get('soyad'), 
        data.get('email'), 
        data.get('sifre'), 
        data.get('rol_id', 3)
    )
    return jsonify(res), 201 if res['success'] else 400

# bu fonksiyon gonderilen email ve sifre bilgilerini alir
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() # gonderilen email ve sifre bilgilerini alir ama json formatinda
    res = auth_service.login_user(data.get('email'), data.get('sifre'))
    return jsonify(res), 200 if res['success'] else 401

# sisteme giris yapmis kullanicinin profil bilgilerini doner
@auth_bp.route('/me', methods=['GET'])
@token_required # iceriye sadece gecerli token ile girilebilmesini sagliyo
def get_me(current_user_rol):
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(" ")[1] 
        data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"]) # gelen tokeni alir cozer ve icindeki bilgileri data'ya atar
        user_id = data['user_id'] # token icindeki id bilgisini user_id'ye atar bu sayede hangi kullanici oldugunu anlariz
        
        user = repo.find_by_id(user_id) # user_id'yi repostirorye gonderir 
        if user:
            if 'sifre' in user: del user['sifre']
            return jsonify({"success": True, "data": user})
        return jsonify({"success": False, "message": "Kullanıcı bulunamadı."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# bu fonksiyon giris yapmis kullanicinin profil bilgilerini guncellemesini saglar
@auth_bp.route('/update-profile', methods=['POST'])
@token_required
def update_profile(current_user_rol):
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(" ")[1]
        user_data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = user_data['user_id'] # token icindeki id bilgisini user_id'ye atar bu sayede hangi kullanici oldugunu anlariz
        
        data = request.get_json() 
        password = data.get('sifre') if data.get('sifre') and len(data.get('sifre')) > 0 else None # sifre gonderilmemisse yani sifre kutusuna bir sey yazilmamissa sifreyi degistirmek istemiyodur
        
        success = repo.update_profile(
            user_id, data.get('ad'), data.get('soyad'), data.get('email'), data.get('avatar'), password
        ) # kullanici bilgilerini guncellemesi icin repositorye gonderir
        if success:
            return jsonify({"success": True, "message": "Profil güncellendi!"})
        return jsonify({"success": False, "message": "Güncelleme başarısız."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# bu fonksiyon tum kullanicilarin listesini doner
@auth_bp.route('/list', methods=['GET'])
@token_required
def get_users(current_user_rol):
    if current_user_rol == 3: 
        return jsonify({"success": False, "message": "Yetkisiz işlem!"}), 403
    users = repo.get_all_users()
    return jsonify({"success": True, "data": users})


# bu fonksiyon id'ye gore kullanici silme islemini yapar
@auth_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user_rol, user_id):
    if current_user_rol != 1: 
        return jsonify({"success": False, "message": "Sadece Yöneticiler!"}), 403
    result = repo.delete_user(user_id) # gonderilen id'yi repositorye gonderir
    if result: 
        return jsonify({"success": True, "message": "Üye silindi."})
    else: 
        return jsonify({"success": False, "message": "Silinemedi."})