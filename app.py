from flask import Flask
from src.controllers.auth_controller import auth_bp
from src.controllers.book_controller import book_bp
from src.controllers.loan_controller import loan_bp
from src.controllers.ui_controller import ui_bp

#app.py : Projenin ana giris kapisidir , Flask uygulamasini baslatir 

app = Flask(__name__)

# Blueprintleri Kaydet
app.register_blueprint(auth_bp) # auth = kimlik dogrulama 
app.register_blueprint(book_bp) # book = kitap islemleri 
app.register_blueprint(loan_bp) # loan = odunc alma 
app.register_blueprint(ui_bp)   # ui = arayuz sayfalari 

if __name__ == '__main__':
    app.run(debug=True)