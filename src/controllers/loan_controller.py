from flask import Blueprint, request, jsonify, render_template
from src.repositories.loan_repository import LoanRepository
from src.utils.decorators import token_required
import jwt
from config import Config

loan_bp = Blueprint('loan_bp', __name__, url_prefix='/loans')
repo = LoanRepository()

# bu fonksiyon kullanicinin kendi odunc aldigi kitaplari listelemesini saglar
@loan_bp.route('/my-loans', methods=['GET'])
@token_required
def get_my_loans(current_user_rol):
    try:
        
        token = request.headers.get('Authorization').split(" ")[1]
        data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"]) # token'dan kullanicinin user id'sini alir
        user_id = data['user_id']
        
        
        loans = repo.get_user_loans(user_id) # kullanicinin id'sini repoya gonderir ve odunc aldigi kitaplari getirir
        return jsonify({"success": True, "data": loans})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# bu fonksiyon admin sayfasinda kullanilmak uzere istatistik verilerini getirir (3 kart)
@loan_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(current_user_rol):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    return jsonify({"success": True, "data": repo.get_stats()})

# bu fonksiyon teslim tarihin gecmis kitaplari getirir
@loan_bp.route('/overdue', methods=['GET'])
@token_required
def get_overdue(current_user_rol):
    all_loans = repo.get_all_active_loans_admin()
    overdue_only = [loan for loan in all_loans if loan['durum'] == 'Gecikti'] # sadece gecikmis olanlari filtreler
    return jsonify({"success": True, "data": overdue_only})

# bu fonksiyon odunc alinan bir kitabin iade islemini yapar
@loan_bp.route('/return/<int:loan_id>', methods=['POST'])
@token_required
def return_book(current_user_rol, loan_id):
    
    if current_user_rol == 3:
        try:
            token = request.headers.get('Authorization').split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            user_id = data['user_id']
            
            # repo yerine direkt sql sorgusu ile kullanici id'si kontrolu yapıyo
            from src.utils.db import db
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT KullaniciID FROM OduncIslemleri WHERE OduncID = ?", (loan_id,))
            row = cursor.fetchone()
            cursor.close(); conn.close()

            if not row or row[0] != user_id: # kullanici id'si eslesmiyorsa
                return jsonify({"success": False, "message": "Yetkisiz işlem!"}), 403
        except:
            return jsonify({"success": False, "message": "Kimlik doğrulama hatası"}), 401

    # Admin ise veya kontrolü geçen öğrenci ise iade işlemini yap
    if repo.return_loan(loan_id): return jsonify({"success": True})
    return jsonify({"success": False})

# bu fonksiyon odunc kaydina ceza ekler
@loan_bp.route('/add-fine', methods=['POST'])
@token_required
def add_fine(current_user_rol):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    data = request.get_json()
    if repo.add_fine(data['loan_id'], data['amount']): return jsonify({"success": True})
    return jsonify({"success": False})

# bu fonksiyon yonetici panelinde ogrencilerin bilgilerini getirir (İncele butonu icin)
@loan_bp.route('/member-details/<int:user_id>', methods=['GET'])
@token_required
def member_details(current_user_rol, user_id):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    data = repo.get_member_details(user_id)
    return jsonify({"success": True, "data": data})

# bu fonksiyon yonetici panelinde grafik verilerini getirir
@loan_bp.route('/charts', methods=['GET'])
@token_required
def get_charts(current_user_rol):
    if current_user_rol == 3: return jsonify({"success": False}), 403
    data = repo.get_chart_data()
    return jsonify({"success": True, "data": data})

# bu fonksiyon kullanicinin karsisina odeme sayfasini getirir
@loan_bp.route('/payment-page', methods=['GET'])
def payment_page():
    return render_template('payment.html')

# bu fonksiyon kullanicinin odenmemis cezalarini getirir
@loan_bp.route('/my-fines', methods=['GET'])
@token_required
def get_my_fines(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
        return jsonify({"success": True, "data": repo.get_unpaid_fines(uid)})
    except: return jsonify({"success": False})

# bu fonksiyon kullanicinin ceza odeme islemini yapar (Odemeyi tamamla butonu)
@loan_bp.route('/pay-fine', methods=['POST'])
@token_required
def pay_fine_api(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        decoded = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        uid = decoded['user_id']
        
        data = request.get_json()
        fine_id = data.get('fine_id') # cezanin id'si
        
        
        result = repo.pay_fine(uid, fine_id)
        
        return jsonify(result) 
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# bu fonksiyon admin sayfasinda tum aktif odunc kitaplari getirir
@loan_bp.route('/active', methods=['GET'])
@token_required
def get_active_loans_admin_api(r):
    data = repo.get_all_active_loans_admin()
    return jsonify({"success": True, "data": data})

# bu fonksiyon admin sayfasinda tum odenmemis cezalari getirir
@loan_bp.route('/fines', methods=['GET'])
@token_required
def get_fines_admin_api(r):
    data = repo.get_all_unpaid_fines_admin()
    return jsonify({"success": True, "data": data})

# bu fonksiyon adminin manuel olarak odunc kaydi olusturmasini saglar
@loan_bp.route('/create', methods=['POST'])
@token_required
def create_loan_api(r):
    data = request.get_json()
    res = repo.create_loan(data.get('email'), data.get('isbn'))
    return jsonify(res)

# bu fonksiyon adminin manuel olarak odunc iade islemi yapmasini saglar
@loan_bp.route('/return', methods=['POST'])
@token_required
def return_book_api(r):
    data = request.get_json()
    if repo.return_loan_by_copy(data.get('kopya_id')):
        return jsonify({"success": True, "message": "Kitap iade alındı!"})
    return jsonify({"success": False, "message": "Hata oluştu."})