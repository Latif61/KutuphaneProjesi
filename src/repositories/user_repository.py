from src.utils.db import db
import pyodbc
from werkzeug.security import generate_password_hash

class UserRepository:
    
    # gelen emaile sahip kullanici var mi diye veritabaninda arar
    def find_by_email(self, email):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM Kullanicilar WHERE Email = ?"
        cursor.execute(sql, (email,))
        row = cursor.fetchone() # eger o emaile sahip kullanici varsa bilgilerini row'a atar
        
        user = None
        if row:
            user = {
                "id": row.KullaniciID,
                "ad": row.Ad,
                "soyad": row.Soyad,
                "email": row.Email,
                "sifre": row.SifreHash,
                "rol_id": row.RolID,
                "avatar": row.Avatar if hasattr(row, 'Avatar') and row.Avatar else 'avatar1'
            }
            
        cursor.close()
        conn.close()
        return user

    # controllerdan gelen id'yi alir ve bu id'ye sahip kullanicinin bilgilerini veritabanindan cagirir
    def find_by_id(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM Kullanicilar WHERE KullaniciID = ?"
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone() # eger o id'ye sahip kullanici varsa bilgilerini row'a atar
        
        user = None
        if row:
            user = {
                "id": row.KullaniciID,
                "ad": row.Ad,
                "soyad": row.Soyad,
                "email": row.Email,
                "sifre": row.SifreHash,
                "rol_id": row.RolID,
                "avatar": row.Avatar if hasattr(row, 'Avatar') and row.Avatar else 'avatar1'
            }
        
        cursor.close()
        conn.close()
        return user

    # bu fonksiyon kullanicinin gonderdigi verileri alir ve veritabanina yeni kullanici kaydi yapar (Kayit olma)
    def create_user(self, ad, soyad, email, hashed_password, rol_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # varsayilan avatar avatar1 oluyo
            sql = """
            INSERT INTO Kullanicilar (Ad, Soyad, Email, SifreHash, RolID, Avatar)
            VALUES (?, ?, ?, ?, ?, 'avatar1')
            """
            cursor.execute(sql, (ad, soyad, email, hashed_password, rol_id))# hazirladigi sql komutunu parametrelerle birlestirip calistirir
            conn.commit() # degisiklikleri kaydeder
            return True
        except pyodbc.IntegrityError:
            return False # Email zaten varsa hata doner
        except Exception as e:
            print(f"Kayıt Hatası: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    # controllerdan gelen kullanici bilgilerini alir ve veritabaninda gunceller
    def update_profile(self, user_id, ad, soyad, email, avatar, sifre=None):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            if sifre:
                # sifre de degisecekse hashleyip kaydediyoruz
                hashed_pw = generate_password_hash(sifre)
                sql = "UPDATE Kullanicilar SET Ad=?, Soyad=?, Email=?, Avatar=?, SifreHash=? WHERE KullaniciID=?"
                cursor.execute(sql, (ad, soyad, email, avatar, hashed_pw, user_id))
            else:
                # sifre degismeyecekse sadece bilgi ve avatar degisecekse
                sql = "UPDATE Kullanicilar SET Ad=?, Soyad=?, Email=?, Avatar=? WHERE KullaniciID=?"
                cursor.execute(sql, (ad, soyad, email, avatar, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Profil Güncelleme Hatası: {e}")
            return False
        finally:
            cursor.close(); conn.close()

    # bu fonksiyon tum kullanicilarin listesini doner
    def get_all_users(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT KullaniciID, Ad, Soyad, Email, RolID, OlusturmaTarihi FROM Kullanicilar ORDER BY OlusturmaTarihi DESC"
        cursor.execute(sql)
        users = cursor.fetchall() # tum kullanicilari cagirir
        
        user_list = []
        for row in users:
            user_list.append({
                "id": row.KullaniciID,
                "ad": row.Ad,
                "soyad": row.Soyad,
                "email": row.Email,
                "rol": row.RolID,
                "tarih": row.OlusturmaTarihi.strftime('%d.%m.%Y') if row.OlusturmaTarihi else "-"
            })
            
        cursor.close()
        conn.close()
        return user_list

    # controllerdan gelen id'ye sahip kullaniciyi veritabanindan siler
    def delete_user(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = "DELETE FROM Kullanicilar WHERE KullaniciID = ?"
            cursor.execute(sql, (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Silme Hatası: {e}")
            return False
        finally:
            cursor.close()
            conn.close()