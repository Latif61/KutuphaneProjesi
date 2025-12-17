from flask import Blueprint, render_template

ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def login_page(): return render_template('login.html')
@ui_bp.route('/panel')
def dashboard_page(): return render_template('dashboard.html')
@ui_bp.route('/books-management')
def books_page(): return render_template('books.html')
@ui_bp.route('/loans-management')
def loans_page(): return render_template('loans.html')
@ui_bp.route('/members')
def members_page(): return render_template('members.html')
@ui_bp.route('/student')
def student_panel(): return render_template('student_dashboard.html')

# --- YENİ EKLENEN ---
@ui_bp.route('/settings')
def settings_page(): return render_template('settings.html')