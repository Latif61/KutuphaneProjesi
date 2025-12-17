from flask import Blueprint, request, jsonify
from src.repositories.book_repository import BookRepository
from src.utils.decorators import token_required
import jwt
from config import Config

book_bp = Blueprint('book_bp', __name__, url_prefix='/books')
repo = BookRepository()

# --- 1. LİSTELEME & ARAMA ---
@book_bp.route('/paginated', methods=['GET'])
@token_required
def paginated(r): 
    return jsonify({"success": True, "data": repo.get_books_paginated(int(request.args.get('page', 1)))})

@book_bp.route('/search', methods=['GET'])
@token_required
def search(r): 
    return jsonify({"success": True, "data": repo.search_books(request.args.get('q'))})

@book_bp.route('/list', methods=['GET']) # Toplam sayı için gerekli
@token_required
def list_all(r): 
    return jsonify({"success": True, "data": repo.get_all_books()})

# --- 2. YORUMLAR ---
@book_bp.route('/comments/<int:book_id>', methods=['GET'])
@token_required
def get_comments(r, book_id):
    return jsonify({"success": True, "data": repo.get_comments(book_id)})

@book_bp.route('/add-comment', methods=['POST'])
@token_required
def add_comment(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
        data = request.get_json()
        if repo.add_comment(uid, data['book_id'], data['text']): return jsonify({"success": True})
        return jsonify({"success": False})
    except: return jsonify({"success": False})

# --- 3. TALEP SİSTEMİ (ÖĞRENCİ & ADMİN) ---
@book_bp.route('/request', methods=['POST'])
@token_required
def req_book(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
        data = request.get_json()
        return jsonify(repo.request_book(uid, data.get('book_id')))
    except Exception as e: return jsonify({"success": False, "message": str(e)})

@book_bp.route('/admin/requests', methods=['GET'])
@token_required
def get_reqs(r):
    return jsonify({"success": True, "data": repo.get_pending_requests()})

@book_bp.route('/admin/process-request', methods=['POST'])
@token_required
def proc_req(r):
    data = request.get_json()
    return jsonify(repo.process_request(data.get('id'), data.get('action')))

# --- 4. DİĞER ---
@book_bp.route('/add', methods=['POST'])
@token_required
def add(r): 
    if repo.add_book(request.get_json()): return jsonify({"success": True})
    return jsonify({"success": False})

# ... (Mevcut kodların altına ekle) ...

# --- FAVORİLER ---
@book_bp.route('/favorite/toggle', methods=['POST'])
@token_required
def toggle_fav(r):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
        data = request.get_json()
        return jsonify(repo.toggle_favorite(uid, data.get('book_id')))
    except: return jsonify({"success": False})

@book_bp.route('/favorites', methods=['GET'])
@token_required
def get_favs(r):
    token = request.headers.get('Authorization').split(" ")[1]
    uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
    return jsonify({"success": True, "data": repo.get_user_favorites(uid)})

@book_bp.route('/favorites/ids', methods=['GET'])
@token_required
def get_fav_ids(r):
    token = request.headers.get('Authorization').split(" ")[1]
    uid = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])['user_id']
    return jsonify({"success": True, "data": repo.get_favorite_ids(uid)})

# ... (Mevcut kodların altına) ...

@book_bp.route('/comment/delete', methods=['POST'])
@token_required
def delete_comment_api(current_user_rol):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        user_data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = user_data['user_id']
        
        data = request.get_json()
        comment_id = data.get('comment_id')
        
        # Repository'e rolü de gönderiyoruz ki Admin mi Öğrenci mi anlasın
        result = repo.delete_comment(comment_id, user_id, current_user_rol)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})