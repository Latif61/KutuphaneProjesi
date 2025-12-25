import os
#Config = ayar = Projenin ayar dosyasidir 
class Config:
    #Secret Key : JWT token şifrelemesi ve oturum güvenliği için kullanılan gizli anahtarı tutar.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bu-cok-gizli-bir-anahtardir-nexus-projesi-2025'
    
    # Mail Konfigürasyonu : Sifre sifirlama ve bildirimler için gerekli e-posta sunucu aylarını barındırır
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')