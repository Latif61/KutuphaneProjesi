import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bu-cok-gizli-bir-anahtardir-nexus-projesi-2025'
    
    # Mail Konfigürasyonu
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')