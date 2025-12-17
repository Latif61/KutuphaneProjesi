from flask import Flask
from src.controllers.auth_controller import auth_bp
from src.controllers.book_controller import book_bp
from src.controllers.loan_controller import loan_bp
from src.controllers.ui_controller import ui_bp

app = Flask(__name__)

# Blueprintleri Kaydet
app.register_blueprint(auth_bp)
app.register_blueprint(book_bp)
app.register_blueprint(loan_bp)
app.register_blueprint(ui_bp)

if __name__ == '__main__':
    app.run(debug=True)