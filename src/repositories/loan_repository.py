from src.utils.db import db
from datetime import datetime, timedelta # timedelta eklendi

class LoanRepository:
    
    # ogrencinin su anda elinde bulunan yani odunc aldigi kitaplari listeler 
    def get_user_loans(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # o.OduncID alanını SELECT sorgusuna ekledik
            sql = """
            SELECT o.OduncID, k.KitapAdi, o.AlisTarihi, o.SonTeslimTarihi,
                   DATEDIFF(day, o.SonTeslimTarihi, GETDATE()) as GecikmeGun,
                   (SELECT SUM(Tutar) FROM Cezalar WHERE OduncID = o.OduncID AND OdendiMi = 0) as Ceza
            FROM OduncIslemleri o
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            WHERE o.KullaniciID = ? AND o.IadeEdildiMi = 0
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            
            loans = []
            for row in rows:
                loans.append({
                    "id": row[0], # JavaScript'in beklediği 'id' buraya eklendi
                    "kitap_adi": row[1],
                    "alis_tarihi": row[2].strftime('%d.%m.%Y') if row[2] else '',
                    "son_teslim": row[3].strftime('%d.%m.%Y') if row[3] else '',
                    "gecikme_gun": row[4] if row[4] and row[4] > 0 else 0,
                    "ceza_tutar": float(row[5]) if row[5] else 0.0
                })
            return loans
        except Exception as e:
            print(f"Hata: {e}")
            return []
        finally:
            cursor.close(); conn.close()

    # bu fonksiyon yonetici panelindeki Durum Kartlarini dolduran fonksiyondur
    def get_stats(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM OduncIslemleri WHERE IadeEdildiMi = 0")
            active = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(Tutar) FROM Cezalar")
            val = cursor.fetchone()[0]
            fines = float(val) if val else 0.0
            cursor.execute("SELECT COUNT(*) FROM Kitaplar")
            books = cursor.fetchone()[0]
            return {"active_loans": active, "total_fines": fines, "total_books": books}
        except: return {"active_loans": 0, "total_fines": 0, "total_books": 0}
        finally: cursor.close(); conn.close()

    # bu fonksiyon odunc verme islemi yapiyo
    def add_loan(self, uid, cid):
        return True 

    # bu fonksiyon kitap iade etme fonksiyondur ama burada zincirleme bir islem yapiyo
    def return_loan(self, lid):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            # Önce KopyaID'yi al
            cursor.execute("SELECT KopyaID FROM OduncIslemleri WHERE OduncID=?", (lid,))
            row = cursor.fetchone()
            if not row: return False
            cid = row[0]

            # islmei güncelle
            cursor.execute("UPDATE OduncIslemleri SET IadeTarihi=?, IadeEdildiMi=1 WHERE OduncID=?", (now, lid))
            # kitabi müsait yap
            cursor.execute("UPDATE KitapKopyalari SET Durum='Musait' WHERE KopyaID=?", (cid,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"İade Hatası: {e}")
            return False
        finally: cursor.close(); conn.close()

    def get_overdue_loans(self): return []
    def add_fine(self, l, a): return True

    # bu fonksiyon ogrencinin su an elinde bulanan kitaplari verir burada yine iliskisel veritabani yapisi var 
    def get_member_details(self, uid):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql_active = "SELECT k.KitapAdi, o.AlisTarihi, o.SonTeslimTarihi FROM OduncIslemleri o JOIN KitapKopyalari kc ON o.KopyaID=kc.KopyaID JOIN Kitaplar k ON kc.KitapID=k.KitapID WHERE o.KullaniciID=? AND o.IadeEdildiMi=0"
            cursor.execute(sql_active, (uid,))
            active = [{"kitap": r[0], "alis": r[1].strftime('%d.%m.%Y'), "teslim": r[2].strftime('%d.%m.%Y')} for r in cursor.fetchall()]
            return {"active_loans": active, "past_loans": [], "total_debt": 0}
        except: return None
        finally: cursor.close(); conn.close()

    # bu fonksiyon en cok oyunan ve en cok okunan kitaplar grafiklerini besleyen yerdir
    def get_chart_data(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql_users = """
            SELECT TOP 5 u.Ad + ' ' + u.Soyad as AdSoyad, COUNT(o.OduncID) as OkumaSayisi
            FROM OduncIslemleri o
            JOIN Kullanicilar u ON o.KullaniciID = u.KullaniciID
            GROUP BY u.Ad, u.Soyad
            ORDER BY OkumaSayisi DESC
            """
            cursor.execute(sql_users)
            top_users = [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]

            sql_books = """
            SELECT TOP 5 k.KitapAdi, COUNT(o.OduncID) as OkunmaSayisi
            FROM OduncIslemleri o
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            GROUP BY k.KitapAdi
            ORDER BY OkunmaSayisi DESC
            """
            cursor.execute(sql_books)
            top_books = [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]

            return {"top_users": top_users, "top_books": top_books}
        except Exception as e:
            print(f"Grafik Hatası: {e}")
            return {"top_users": [], "top_books": []}
        finally:
            cursor.close(); conn.close()

    # bu fonksiyon ogrencinin henuz odenmemis cezalarini getirir
    def get_unpaid_fines(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            SELECT c.CezaID, k.KitapAdi, c.Tutar, o.SonTeslimTarihi
            FROM Cezalar c
            JOIN OduncIslemleri o ON c.OduncID = o.OduncID
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            WHERE o.KullaniciID = ? AND c.OdendiMi = 0
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return [{
                "id": r.CezaID, "kitap": r.KitapAdi, "tutar": float(r.Tutar), "tarih": r.SonTeslimTarihi.strftime('%d.%m.%Y')
            } for r in rows]
        except Exception as e:
            print(e)
            return []
        finally: cursor.close(); conn.close()

    # bu fonksiyon kullanicinin borclarini odemesini saglar
    def pay_fine(self, user_id, fine_id=None):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            if fine_id:
                # Sadece secilen bir cezayı öde
                sql = "UPDATE Cezalar SET OdendiMi = 1, OdemeTarihi = GETDATE() WHERE CezaID = ?"
                cursor.execute(sql, (fine_id,))
            else:
                # Kullanıcının TÜM ödenmemiş borçlarını öde
                sql = """
                UPDATE Cezalar SET OdendiMi = 1, OdemeTarihi = GETDATE() 
                WHERE OdendiMi = 0 AND OduncID IN (
                    SELECT OduncID FROM OduncIslemleri WHERE KullaniciID = ?
                )
                """
                cursor.execute(sql, (user_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Ödeme Hatası: {e}")
            return False
        finally: cursor.close(); conn.close()

    # bu fonksiyon su an kullanicilarda olan iade edilmemis tum kitaplari listelemeye yarar
    def get_all_active_loans_admin(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            SELECT o.OduncID, k.KitapAdi, u.Ad + ' ' + u.Soyad as Okuyucu, 
                   o.SonTeslimTarihi, o.KopyaID,
                   CASE WHEN GETDATE() > o.SonTeslimTarihi THEN 'Gecikti' ELSE 'Devam Ediyor' END as Durum
            FROM OduncIslemleri o
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            JOIN Kullanicilar u ON o.KullaniciID = u.KullaniciID
            WHERE o.IadeEdildiMi = 0
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [{
                "id": r.OduncID, "kitap": r.KitapAdi, "okuyucu": r.Okuyucu,
                "son_teslim": r.SonTeslimTarihi.strftime('%d.%m.%Y'),
                "kopya_id": r.KopyaID, "durum": r.Durum
            } for r in rows]
        except: return []
        finally: cursor.close(); conn.close()

    # bu fonksiyon odenmemis cezalarin tamamini listelemeye yarar 
    def get_all_unpaid_fines_admin(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            SELECT u.Ad + ' ' + u.Soyad as Uye, k.KitapAdi, o.SonTeslimTarihi, c.Tutar
            FROM Cezalar c
            JOIN OduncIslemleri o ON c.OduncID = o.OduncID
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            JOIN Kullanicilar u ON o.KullaniciID = u.KullaniciID
            WHERE c.OdendiMi = 0
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            fines = []
            for r in rows:
                fines.append({
                    "uye": r[0], "kitap": r[1], 
                    "tarih": r[2].strftime('%d.%m.%Y') if r[2] else "-", 
                    "borc": float(r[3]) if r[3] else 0.0
                })
            return fines
        except Exception as e:
            print(f"Hata: {e}")
            return []
        finally: cursor.close(); conn.close()

    #  
    def return_loan_by_copy(self, kopya_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            cursor.execute("UPDATE OduncIslemleri SET IadeTarihi=?, IadeEdildiMi=1 WHERE KopyaID=? AND IadeEdildiMi=0", (now, kopya_id))
            cursor.execute("UPDATE KitapKopyalari SET Durum='Musait' WHERE KopyaID=?", (kopya_id,))
            conn.commit()
            return True
        except: return False
        finally: cursor.close(); conn.close()
    
    # 
    def create_loan(self, email, isbn):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Kullanıcıyı bul
            cursor.execute("SELECT KullaniciID FROM Kullanicilar WHERE Email = ?", (email,))
            user = cursor.fetchone()
            if not user: return {"success": False, "message": "Kullanıcı bulunamadı."}
            user_id = user[0]

            # 2. Kitabın müsait bir kopyasını bul
            cursor.execute("""
                SELECT TOP 1 kc.KopyaID 
                FROM KitapKopyalari kc
                JOIN Kitaplar k ON kc.KitapID = k.KitapID
                WHERE k.ISBN = ? AND kc.Durum = 'Musait'
            """, (isbn,))
            copy = cursor.fetchone()
            if not copy: return {"success": False, "message": "Bu kitabın müsait kopyası yok!"}
            copy_id = copy[0]

            # 3. Ödünç işlemini kaydet
            now = datetime.now()
            due = now + timedelta(days=15)
            sql = "INSERT INTO OduncIslemleri (KopyaID, KullaniciID, AlisTarihi, SonTeslimTarihi, IadeEdildiMi) VALUES (?, ?, ?, ?, 0)"
            cursor.execute(sql, (copy_id, user_id, now, due))
            
            # 4. Kopyayı 'Oduncte' olarak işaretle
            cursor.execute("UPDATE KitapKopyalari SET Durum = 'Oduncte' WHERE KopyaID = ?", (copy_id,))
            
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            cursor.close(); conn.close()