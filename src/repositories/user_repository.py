from src.utils.db import db
import pyodbc
from werkzeug.security import generate_password_hash

# kullanicilerle ilgili veritabani sorgularini (SQL) tutan dosyadir (mutfak)

class UserRepository:
    # --- 1. GİRİŞ İÇİN GEREKLİ ---
    def find_by_email(self, email):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM Kullanicilar WHERE Email = ?"
        cursor.execute(sql, (email,))
        row = cursor.fetchone()
        
        user = None
        if row:
            user = {
                "id": row.KullaniciID,
                "ad": row.Ad,
                "soyad": row.Soyad,
                "email": row.Email,
                "sifre": row.SifreHash,
                "rol_id": row.RolID,
                # Avatar sütunu yeni eklendiği için kontrol ediyoruz
                "avatar": row.Avatar if hasattr(row, 'Avatar') and row.Avatar else 'avatar1'
            }
            
        cursor.close()
        conn.close()
        return user

    # --- 2. ID İLE BULMA (PROFİL AYARLARI İÇİN) ---
    def find_by_id(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM Kullanicilar WHERE KullaniciID = ?"
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        
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

    # --- 3. KAYIT OLMA ---
    def create_user(self, ad, soyad, email, hashed_password, rol_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Avatar varsayılan olarak 'avatar1' olsun
            sql = """
            INSERT INTO Kullanicilar (Ad, Soyad, Email, SifreHash, RolID, Avatar)
            VALUES (?, ?, ?, ?, ?, 'avatar1')
            """
            cursor.execute(sql, (ad, soyad, email, hashed_password, rol_id))
            conn.commit()
            return True
        except pyodbc.IntegrityError:
            return False # Email zaten var
        except Exception as e:
            print(f"Kayıt Hatası: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    # --- 4. PROFİL GÜNCELLEME ---
    def update_profile(self, user_id, ad, soyad, email, avatar, sifre=None):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            if sifre:
                # Şifre de değişecekse hashleyip kaydediyoruz
                hashed_pw = generate_password_hash(sifre)
                sql = "UPDATE Kullanicilar SET Ad=?, Soyad=?, Email=?, Avatar=?, SifreHash=? WHERE KullaniciID=?"
                cursor.execute(sql, (ad, soyad, email, avatar, hashed_pw, user_id))
            else:
                # Sadece bilgi ve avatar değişecekse
                sql = "UPDATE Kullanicilar SET Ad=?, Soyad=?, Email=?, Avatar=? WHERE KullaniciID=?"
                cursor.execute(sql, (ad, soyad, email, avatar, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Profil Güncelleme Hatası: {e}")
            return False
        finally:
            cursor.close(); conn.close()

    # --- 5. ÜYE LİSTELEME ---
    def get_all_users(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT KullaniciID, Ad, Soyad, Email, RolID, OlusturmaTarihi FROM Kullanicilar ORDER BY OlusturmaTarihi DESC"
        cursor.execute(sql)
        users = cursor.fetchall()
        
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

    # --- 6. ÜYE SİLME ---
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