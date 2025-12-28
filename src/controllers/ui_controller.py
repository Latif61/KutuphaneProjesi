from flask import Blueprint, render_template

ui_bp = Blueprint('ui', __name__)

# Sitenin acilis sayfasini ekrana getirir yani login sayfasini acar
@ui_bp.route('/')
def login_page(): return render_template('login.html')

# kullanici giris yaptiktan sonra karsilastigi ana yonetim ekranini acmaya yarar
@ui_bp.route('/panel')
def dashboard_page(): return render_template('dashboard.html')

# kitap yonetim sayfasini acmaya yarar
@ui_bp.route('/books-management')
def books_page(): return render_template('books.html')

# odunc islemleri yonetim sayfasini acmaya yarar
@ui_bp.route('/loans-management') # kitap odunc islemlerinin yapildigi sayfayi acar
def loans_page(): return render_template('loans.html') 

# uyeler yonetim sayfasini acmaya yarar
@ui_bp.route('/members') 
def members_page(): return render_template('members.html')

# ogrenci paneli sayfasini acmaya yarar
@ui_bp.route('/student')
def student_panel(): return render_template('student_dashboard.html')

# ayarlar sayfasini acmaya yarar
@ui_bp.route('/settings')
def settings_page(): return render_template('settings.html')

# kayit olma sayfasini acmaya yarar
@ui_bp.route('/register')
def register_page():
    return render_template('register.html')