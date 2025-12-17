from src.utils.db import db
from datetime import datetime

class LoanRepository:
    
    # --- 1. ÖĞRENCİNİN KİTAPLARI (BU FONKSİYON ŞART) ---
    def get_user_loans(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # Kitap adı, alış tarihi, son teslim tarihi ve ceza bilgisini çekiyoruz
            sql = """
            SELECT k.KitapAdi, o.AlisTarihi, o.SonTeslimTarihi,
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
                    "kitap_adi": row.KitapAdi,
                    "alis_tarihi": row.AlisTarihi.strftime('%d.%m.%Y'),
                    "son_teslim": row.SonTeslimTarihi.strftime('%d.%m.%Y'),
                    "gecikme_gun": row.GecikmeGun if row.GecikmeGun and row.GecikmeGun > 0 else 0,
                    "ceza_tutar": float(row.Ceza) if row.Ceza else 0.0
                })
            return loans
        except Exception as e:
            print(f"Hata: {e}")
            return []
        finally:
            cursor.close(); conn.close()

    # --- 2. İSTATİSTİKLER ---
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

    # --- 3. DİĞER FONKSİYONLAR (Ödünç Verme, İade, vb.) ---
    def add_loan(self, uid, cid):
        # Bu fonksiyon admin tarafinda kullanilir
        return True 

    def return_loan(self, lid):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            cursor.execute("UPDATE OduncIslemleri SET IadeTarihi=?, IadeEdildiMi=1 WHERE OduncID=?", (now, lid))
            cursor.execute("SELECT KopyaID FROM OduncIslemleri WHERE OduncID=?", (lid,))
            cid = cursor.fetchone()[0]
            cursor.execute("UPDATE KitapKopyalari SET Durum='Musait' WHERE KopyaID=?", (cid,))
            conn.commit()
            return True
        except: return False
        finally: cursor.close(); conn.close()

    def get_overdue_loans(self): return []
    def add_fine(self, l, a): return True
    
    def get_member_details(self, uid):
        # Adminin üye kartı için baktığı yer
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql_active = "SELECT k.KitapAdi, o.AlisTarihi, o.SonTeslimTarihi FROM OduncIslemleri o JOIN KitapKopyalari kc ON o.KopyaID=kc.KopyaID JOIN Kitaplar k ON kc.KitapID=k.KitapID WHERE o.KullaniciID=? AND o.IadeEdildiMi=0"
            cursor.execute(sql_active, (uid,))
            active = [{"kitap": r[0], "alis": r[1].strftime('%d.%m.%Y'), "teslim": r[2].strftime('%d.%m.%Y')} for r in cursor.fetchall()]
            return {"active_loans": active, "past_loans": [], "total_debt": 0}
        except: return None
        finally: cursor.close(); conn.close()

# ... (Mevcut kodlar yukarıda kalsın) ...

    # --- 8. GRAFİK VERİLERİ (YENİ) ---
    def get_chart_data(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. EN ÇOK OKUYAN 5 ÖĞRENCİ
            sql_users = """
            SELECT TOP 5 u.Ad + ' ' + u.Soyad as AdSoyad, COUNT(o.OduncID) as OkumaSayisi
            FROM OduncIslemleri o
            JOIN Kullanicilar u ON o.KullaniciID = u.KullaniciID
            GROUP BY u.Ad, u.Soyad
            ORDER BY OkumaSayisi DESC
            """
            cursor.execute(sql_users)
            top_users = [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]

            # 2. EN ÇOK OKUNAN 5 KİTAP
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

# ... (Mevcut kodların altına ekle) ...

    # --- 10. ÖDENMEMİŞ CEZALARI GETİR ---
    def get_unpaid_fines(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # Hangi kitaptan ceza yediğini de gösterelim
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
                "id": r.CezaID,
                "kitap": r.KitapAdi,
                "tutar": float(r.Tutar),
                "tarih": r.SonTeslimTarihi.strftime('%d.%m.%Y')
            } for r in rows]
        except Exception as e:
            print(e)
            return []
        finally: cursor.close(); conn.close()

    # --- 11. CEZA ÖDE (Para Tahsilatı) ---
    def pay_fine(self, fine_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # Ödendi olarak işaretle ve bugünün tarihini at
            sql = "UPDATE Cezalar SET OdendiMi = 1, OdemeTarihi = GETDATE() WHERE CezaID = ?"
            cursor.execute(sql, (fine_id,))
            conn.commit()
            return True
        except: return False
        finally: cursor.close(); conn.close()