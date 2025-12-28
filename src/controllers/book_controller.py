from flask import Blueprint, request, jsonify
from src.repositories.book_repository import BookRepository
from src.utils.decorators import token_required
import jwt
from config import Config

# book_controller.py = kitaplarla ilgili API rotalarini (endpoint) yonetir yani garson görevi görür , istegi alir mutfaga(reporstiry) iletir , cevap getirir 

book_bp = Blueprint('book_bp', __name__, url_prefix='/books')
repo = BookRepository()

# bu fonksiyon kutuphanedeki kitaplari sayfa sayfa listelemeye yarar
@book_bp.route('/paginated', methods=['GET'])
@token_required
def paginated(r): 
    return jsonify({"success": True, "data": repo.get_books_paginated(int(request.args.get('page', 1)))}) # sayfa numarasina gore kitaplari getirir ('paga' , 2 yazsaydi 2.sayfdakileri getirirdi)
    # return jsonify cekilen kitaplari json formatinda frontende gonderir

# bu fonksiyon kullanicinin arama yapmasini saglar
@book_bp.route('/search', methods=['GET'])
@token_required
def search(r): 
    return jsonify({"success": True, "data": repo.search_books(request.args.get('q'))}) # yakaladigi kelimeyi repoya gonderir

# kutuphanedeki tum kitaplari tek seferde listelemeye yarar ama benim icin toplam kitap sayisi icin gerekli bir fonksiyon
@book_bp.route('/list', methods=['GET']) 
@token_required
def list_all(r): 
    return jsonify({"success": True, "data": repo.get_all_books()})

# bu fonksiyon bir kitabin detay sayfasina girildiginde o kitaba yapilan yorumlari getirir
@book_bp.route('/comments/<int:book_id>', methods=['GET']) # kitap id'si ile hangi kitabin yorumlarinin getirilecegini belirler
@token_required
def get_comments(r, book_id):
    return jsonify({"success": True, "data": repo.get_comments(book_id)}) # kitap id'sini repoya gonderir ve yorumlari getirir

# bu kitap kullanicilarin bir kitap hakkinda yorum yapmasini saglar
@book_bp.route('/add-comment', methods=['POST'])
@token_required
def add_comment(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id'] # gelen token'i cozer icinden user id'yi alir bu sayede kullaniciyi kim oldugunu anlar
        data = request.get_json() # kullanicidan gelen json verisini alir
        if repo.add_comment(uid, data['book_id'], data['text']): return jsonify({"success": True}) # repoya kullanici id'sini kitap idsini ve yorum metnini gonderir
        return jsonify({"success": False})
    except: return jsonify({"success": False})

# bu fonksiyon kullanicinin kitap talep etmesini saglar
@book_bp.route('/request', methods=['POST'])
@token_required
def req_book(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
        data = request.get_json()
        return jsonify(repo.request_book(uid, data.get('book_id')))
    except Exception as e: return jsonify({"success": False, "message": str(e)})

# bu fonksiyon yoneticinin bekleyen kitap taleplerini listelemesini saglar
@book_bp.route('/admin/requests', methods=['GET'])
@token_required
def get_reqs(r):
    return jsonify({"success": True, "data": repo.get_pending_requests()})

# bu fonksiyon istek olarak gelen kitabi onaylamayi ya da reddetmeyi saglar
@book_bp.route('/admin/process-request', methods=['POST'])
@token_required
def proc_req(r):
    data = request.get_json()
    return jsonify(repo.process_request(data.get('id'), data.get('action')))

# bu fonksiyon kutuphaneye yeni kitap eklemeyi saglar
@book_bp.route('/add', methods=['POST'])
@token_required
def add(r): 
    if repo.add_book(request.get_json()): return jsonify({"success": True}) # yonetici panelinden gonderilen kitap bilgilerini json formatinda alir ve repoya gonderir
    return jsonify({"success": False})

# bu fonksiyon kullanicinin kitaplari favorilere eklemesini veya favorilerden cikarmasini saglar
@book_bp.route('/favorite/toggle', methods=['POST'])
@token_required
def toggle_fav(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id'] # bu islemin kime ait oldugunu belirlemek icin
        data = request.get_json() 
        return jsonify(repo.toggle_favorite(uid, data.get('book_id'))) # kullanici id'si ve kitap id'sini repoya gonderir
    except: return jsonify({"success": False})

# bu fonksiyon kullanicinin favori kitaplarini listelemeyi saglar
@book_bp.route('/favorites', methods=['GET'])
@token_required
def get_favs(r):
    token = request.headers.get('Authorization').split(" ")[1]
    uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id'] # bu islemin kime ait oldugunu belirlemek icin user id'sini alir
    return jsonify({"success": True, "data": repo.get_user_favorites(uid)}) # kullanicinin id'sini repoya gonderir ve favori kitaplarini getirir


# bu fonksiyon kullanicinin favori kitaplarinin sadece id'lerini listelemeyi saglar
@book_bp.route('/favorites/ids', methods=['GET'])
@token_required
def get_fav_ids(r):
    token = request.headers.get('Authorization').split(" ")[1]
    uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
    return jsonify({"success": True, "data": repo.get_favorite_ids(uid)})

# bu fonksiyon kitap yorumunu silmeyi saglar
@book_bp.route('/comment/delete', methods=['POST'])
@token_required
def delete_comment_api(current_user_rol):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        user_data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"]) # token'dan kullanicinin user id'sini alir bu sayede kimin yorum sildigini anlariz
        user_id = user_data['user_id'] 
        
        data = request.get_json() 
        comment_id = data.get('comment_id') 
        
        result = repo.delete_comment(comment_id, user_id, current_user_rol) # repoya yorum id'sini kullanici id'sini ve kullanici rolunu gonderir
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    

# bu fonksiyon kitap silmeyi saglar
@book_bp.route('/delete/<int:book_id>', methods=['DELETE'])
@token_required
def delete_book_api(current_user_rol, book_id):
    
    if current_user_rol == 3: # ogrenci kitap silemez
        return jsonify({"success": False, "message": "Yetkisiz işlem! Öğrenciler kitap silemez."}), 403
    
    if repo.delete_book(book_id): # repoya kitap id'sini gonderir
        return jsonify({"success": True, "message": "Kitap başarıyla silindi."})
    else:
        return jsonify({"success": False, "message": "Kitap silinemedi. Bu kitaba bağlı kopyalar veya işlemler olabilir."})


# bu fonksiyon var olan kitap bilgilerini guncellemeyi saglar
@book_bp.route('/update/<int:book_id>', methods=['PUT']) # kitap id'sine gore hangi kitabin guncellenecegini belirler
@token_required
def update_book_api(current_user_rol, book_id):
    if current_user_rol == 3: # ogrenci kitap guncelleyemez
        return jsonify({"success": False, "message": "Yetkisiz işlem!"}), 403
    
    data = request.get_json()
    if repo.update_book(book_id, data): # repoya kitap id'sini ve guncel verileri gonderir 
        return jsonify({"success": True, "message": "Kitap başarıyla güncellendi!"})
    return jsonify({"success": False, "message": "Güncelleme başarısız."})

# bu fonksiyon kutuphanedeki kitap kategorilerini getirir
@book_bp.route('/categories', methods=['GET'])
@token_required
def get_categories(current_user_rol):
    data = repo.get_all_categories()
    return jsonify(data)

# bu fonksiyon kutuphaneye yeni kitap kopyasi eklemeyi saglar
@book_bp.route('/add-copy', methods=['POST'])
@token_required
def add_copy(current_user_rol):
    if current_user_rol == 3: # Öğrenci kopya ekleyemez
        return jsonify({"success": False, "message": "Yetkisiz işlem!"}), 403
    
    data = request.get_json() 
    if repo.add_book_copy(data):
        return jsonify({"success": True, "message": "Kopya başarıyla eklendi."})
    return jsonify({"success": False, "message": "Kopya eklenirken hata oluştu."})


# bu fonksiyon kutuphanedeki kitap kategorilerine gore istatistikleri getirir
@book_bp.route('/stats/categories', methods=['GET'])
@token_required
def get_category_stats(current_user_rol):
    # Veritabanından istatistikleri al ve JSON olarak gönder
    data = repo.get_category_distribution()
    return jsonify(data)