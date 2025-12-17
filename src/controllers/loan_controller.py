from flask import Blueprint, request, jsonify, render_template
from src.repositories.loan_repository import LoanRepository
from src.utils.decorators import token_required
import jwt
from config import Config

loan_bp = Blueprint('loan_bp', __name__, url_prefix='/loans')
repo = LoanRepository()

# --- 1. ÖĞRENCİNİN KİTAPLARI (BU EKSİKTİ!) ---
@loan_bp.route('/my-loans', methods=['GET'])
@token_required
def get_my_loans(current_user_rol):
    try:
        # Token'dan User ID'yi çözüyoruz
        token = request.headers.get('Authorization').split(" ")[1]
        data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = data['user_id']
        
        # O ID'ye ait kitapları getir
        loans = repo.get_user_loans(user_id)
        return jsonify({"success": True, "data": loans})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# --- 2. İSTATİSTİKLER (ADMİN İÇİN) ---
@loan_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(current_user_rol):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    return jsonify({"success": True, "data": repo.get_stats()})

# --- 3. GECİKMİŞ KİTAPLAR ---
@loan_bp.route('/overdue', methods=['GET'])
@token_required
def get_overdue(current_user_rol):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    return jsonify({"success": True, "data": repo.get_overdue_loans()})

# --- 4. İADE ET ---
@loan_bp.route('/return/<int:loan_id>', methods=['POST'])
@token_required
def return_book(current_user_rol, loan_id):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    if repo.return_loan(loan_id): return jsonify({"success": True})
    return jsonify({"success": False})

# --- 5. CEZA EKLE ---
@loan_bp.route('/add-fine', methods=['POST'])
@token_required
def add_fine(current_user_rol):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    data = request.get_json()
    if repo.add_fine(data['loan_id'], data['amount']): return jsonify({"success": True})
    return jsonify({"success": False})

# --- 6. ÜYE DETAYLARI (KİMLİK KARTI İÇİN) ---
@loan_bp.route('/member-details/<int:user_id>', methods=['GET'])
@token_required
def member_details(current_user_rol, user_id):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    data = repo.get_member_details(user_id)
    return jsonify({"success": True, "data": data})

# ... (Mevcut kodlar yukarıda kalsın) ...

# --- 7. GRAFİK VERİSİ ---
@loan_bp.route('/charts', methods=['GET'])
@token_required
def get_charts(current_user_rol):
    # Sadece Admin görebilir
    if current_user_rol == 3: return jsonify({"success": False}), 403
    
    data = repo.get_chart_data()
    return jsonify({"success": True, "data": data})

# ... (Mevcut kodların altına ekle) ...

# --- ÖDEME SAYFASI (HTML) ---
@loan_bp.route('/payment-page', methods=['GET'])
def payment_page():
    # Direkt HTML sayfasını döndürüyoruz
    return render_template('payment.html')

# --- BORÇLARI LİSTELE (API) ---
@loan_bp.route('/my-fines', methods=['GET'])
@token_required
def get_my_fines(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
        return jsonify({"success": True, "data": repo.get_unpaid_fines(uid)})
    except: return jsonify({"success": False})

# --- ÖDEME YAP (API) ---
@loan_bp.route('/pay-fine', methods=['POST'])
@token_required
def pay_fine_api(r):
    data = request.get_json()
    if repo.pay_fine(data.get('fine_id')):
        return jsonify({"success": True, "message": "Ödeme başarıyla alındı!"})
    return jsonify({"success": False, "message": "Ödeme işlemi başarısız."})