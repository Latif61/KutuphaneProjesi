import jwt
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
from src.repositories.user_repository import UserRepository
from config import Config

class AuthService:
    def __init__(self):
        self.repo = UserRepository()

    # --- 3. KISIM: HOŞ GELDİN MAİLİ GÖNDERME FONKSİYONU ---
    def _send_welcome_email(self, recipient_email, user_name):
        """Kayıt olan her kullanıcıya kendi adresine hoş geldin maili gönderir."""
        try:
            subject = "Nexus Kütüphanesi'ne Hoş Geldiniz!"
            body = f"""
            Merhaba {user_name},
            
            Kütüphane takip sistemimize başarıyla kayıt oldunuz. 
            Artık sistem üzerinden kitapları inceleyebilir, favorilerinize ekleyebilir 
             ve ödünç alma taleplerinizi yönetebilirsiniz.
            
            Keyifli okumalar dileriz!
            """
            
            msg = MIMEMultipart()
            msg['From'] = Config.MAIL_USERNAME
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # SMTP Sunucusuna bağlan ve gönder
            # Buradaki MAIL_SERVER ve MAIL_PORT bilgileri .env dosyasından gelir
            server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
            server.starttls() # Güvenli bağlantıyı başlat
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"✅ Hoş geldin maili gönderildi: {recipient_email}")
            return True
        except Exception as e:
            # Eğer .env dosyasındaki mail ayarların yanlışsa burada hata basar
            print(f"❌ Mail gönderme hatası: {e}")
            return False

    # --- KAYIT VE OTOMATİK GİRİŞ ---
    def register_user(self, ad, soyad, email, sifre, rol_id):
        hashed_password = generate_password_hash(sifre)
        
        # 1. Kullanıcıyı veritabanına kaydet
        if self.repo.create_user(ad, soyad, email, hashed_password, rol_id):
            
            # 2. Hoş geldin mailini gönder (Yukarıdaki 3. kısım fonksiyonu)
            self._send_welcome_email(email, f"{ad} {soyad}")
            
            # 3. Otomatik giriş için kullanıcıyı bul ve Token üret
            user = self.repo.find_by_email(email)
            if user:
                token = jwt.encode({
                    'user_id': user['id'],
                    'rol_id': user['rol_id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, Config.SECRET_KEY, algorithm="HS256")
                
                return {
                    "success": True, 
                    "token": token, 
                    "role": user['rol_id'], 
                    "user": f"{user['ad']} {user['soyad']}"
                }
        
        return {"success": False, "message": "Kayıt başarısız"}

    # --- GİRİŞ YAPMA ---
    def login_user(self, email, sifre):
        user = self.repo.find_by_email(email)
        if user:
            db_password = str(user['sifre'])
            input_password = str(sifre)
            is_valid = False
            
            # Hem düz metin hem de hash kontrolü yapıyoruz
            if db_password == input_password: is_valid = True
            else:
                try:
                    if check_password_hash(db_password, input_password): is_valid = True
                except: pass

            if is_valid:
                token = jwt.encode({
                    'user_id': user['id'],
                    'rol_id': user['rol_id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                }, Config.SECRET_KEY, algorithm="HS256")
                return {"success": True, "token": token, "role": user['rol_id'], "user": f"{user['ad']} {user['soyad']}"}
        
        return {"success": False, "message": "Hatalı Giriş"}