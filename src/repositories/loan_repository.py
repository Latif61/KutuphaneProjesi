from src.utils.db import db
from datetime import datetime, timedelta # timedelta eklendi

class LoanRepository:
    
    # ogrencinin su anda elinde bulunan yani odunc aldigi kitaplari listeler 
    def get_user_loans(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # DİKKAT: DATEDIFF(day, ...) yerine DATEDIFF(minute, ...) kullandık.
            # Ayrıca Ceza tablosuna bakmak yerine anlık olarak (Dakika * 1 TL) ceza hesaplıyoruz.
            sql = """
            SELECT o.OduncID, k.KitapAdi, o.AlisTarihi, o.SonTeslimTarihi,
                   DATEDIFF(minute, o.SonTeslimTarihi, GETDATE()) as GecikmeDakika,
                   CASE 
                       WHEN GETDATE() > o.SonTeslimTarihi THEN DATEDIFF(minute, o.SonTeslimTarihi, GETDATE()) * 1.0 
                       ELSE 0 
                   END as TahminiCeza
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
                    "id": row[0],
                    "kitap_adi": row[1],
                    "alis_tarihi": row[2].strftime('%d.%m.%Y %H:%M') if row[2] else '', # Saat de görünsün
                    "son_teslim": row[3].strftime('%d.%m.%Y %H:%M') if row[3] else '', # Saat de görünsün
                    "gecikme_gun": row[4] if row[4] and row[4] > 0 else 0, # Dakikayı gün gibi gönderiyoruz ki uyarı çıksın
                    "ceza_tutar": float(row[5]) if row[5] else 0.0
                })
            return loans
        except Exception as e:
            print(f"Hata: {e}")
            return []
        finally:
            cursor.close(); conn.close()

    # bu fonksiyon yonetici panelindeki Durum Kartlarini dolduran fonksiyondur
    # --- İSTATİSTİKLER (GÜNCELLENDİ: SADECE ÖDENMEMİŞ BORÇLAR) ---
    # --- İSTATİSTİKLER (GÜNCELLENDİ: CANLI + KESİNLEŞMİŞ TOPLAM) ---
    def get_stats(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Aktif Ödünç Sayısı
            cursor.execute("SELECT COUNT(*) FROM OduncIslemleri WHERE IadeEdildiMi = 0")
            active = cursor.fetchone()[0]

            # 2. Kesinleşmiş (Tabloya Yazılmış) Cezalar
            cursor.execute("SELECT SUM(Tutar) FROM Cezalar WHERE OdendiMi = 0")
            val_static = cursor.fetchone()[0]
            static_fines = float(val_static) if val_static else 0.0

            # 3. Canlı (Şu An İşleyen) Cezalar
            # İade edilmemiş ve süresi geçmiş kitapların dakika farkını topla (Dakikası 1 TL)
            sql_dynamic = """
            SELECT SUM(DATEDIFF(minute, SonTeslimTarihi, GETDATE())) 
            FROM OduncIslemleri 
            WHERE IadeEdildiMi = 0 AND GETDATE() > SonTeslimTarihi
            """
            cursor.execute(sql_dynamic)
            val_dynamic = cursor.fetchone()[0]
            dynamic_fines = float(val_dynamic) if val_dynamic else 0.0

            # 4. Hepsini Topla
            total_receivable = static_fines + dynamic_fines

            # 5. Toplam Kitap Sayısı
            cursor.execute("SELECT COUNT(*) FROM Kitaplar")
            books = cursor.fetchone()[0]

            return {
                "active_loans": active, 
                "total_fines": total_receivable, # Artık hem eskileri hem yenileri içeriyor
                "total_books": books
            }
        except Exception as e:
            print(f"İstatistik Hatası: {e}")
            return {"active_loans": 0, "total_fines": 0, "total_books": 0}
        finally: cursor.close(); conn.close()

    # bu fonksiyon odunc verme islemi yapiyo
    def add_loan(self, uid, cid):
        return True 

    # bu fonksiyon kitap iade etme fonksiyondur ama burada zincirleme bir islem yapiyo
    # --- BUHARLAŞMAYI ENGELLEYEN İADE FONKSİYONU ---
    # --- SQL HATASI GİDERİLMİŞ İADE FONKSİYONU ---
    def return_loan(self, lid):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Kayıt var mı kontrol et
            cursor.execute("SELECT KopyaID, KullaniciID, SonTeslimTarihi, IadeEdildiMi FROM OduncIslemleri WHERE OduncID = ?", (lid,))
            row = cursor.fetchone()
            
            if not row: 
                return {"success": False, "message": "Kayıt bulunamadı! (OduncID geçersiz)"}
            
            cid = row[0]
            is_returned = row[3]

            if is_returned: 
                return {"success": False, "message": "Bu kitap zaten iade edilmiş!"}

            # 2. Gecikme Hesapla (SQL ile Saniye Bazlı)
            sql_calc = """
            SELECT DATEDIFF(SECOND, SonTeslimTarihi, GETDATE()) as GecikmeSaniye
            FROM OduncIslemleri WHERE OduncID = ?
            """
            cursor.execute(sql_calc, (lid,))
            sec_row = cursor.fetchone()
            gecikme_saniye = int(sec_row[0]) if sec_row else 0

            # 3. Ceza Hesapla (Yukarı Yuvarlama)
            if gecikme_saniye > 0:
                gecikme_dakika = (gecikme_saniye + 59) // 60 
                ceza_tutari = gecikme_dakika * 1.0
                
                # DÜZELTME BURADA: 'OlusturmaTarihi' alanını sorgudan sildik.
                # Veritabanında bu sütun olmadığı için hata veriyordu.
                sql_ceza = "INSERT INTO Cezalar (OduncID, Tutar, OdendiMi) VALUES (?, ?, 0)"
                cursor.execute(sql_ceza, (lid, ceza_tutari))
            
            # 4. İade İşlemi
            cursor.execute("UPDATE OduncIslemleri SET IadeTarihi=GETDATE(), IadeEdildiMi=1 WHERE OduncID=?", (lid,))
            cursor.execute("UPDATE KitapKopyalari SET Durum='Musait', DurumID=1 WHERE KopyaID=?", (cid,))
            
            conn.commit()
            return {"success": True, "message": "İade işlemi başarılı!"}
            
        except Exception as e:
            print(f"❌ İADE HATASI DETAYI: {str(e)}")
            return {"success": False, "message": f"Sistem Hatası: {str(e)}"}
        finally: 
            cursor.close(); conn.close()

    # bu fonksiyon ogrencinin su an elinde bulanan kitaplari verir burada yine iliskisel veritabani yapisi var 
    # --- ÜYE DETAYLARI (GÜNCELLENDİ: GEÇMİŞ + BORÇ HESABI EKLENDİ) ---
    # --- ÜYE DETAYLARI (GÜNCELLENDİ: TEKRARSIZ KİTAP LİSTESİ) ---
    def get_member_details(self, uid):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Aktif Ödünçler (Burası aynı kalıyor)
            sql_active = """
            SELECT k.KitapAdi, o.AlisTarihi, o.SonTeslimTarihi 
            FROM OduncIslemleri o 
            JOIN KitapKopyalari kc ON o.KopyaID=kc.KopyaID 
            JOIN Kitaplar k ON kc.KitapID=k.KitapID 
            WHERE o.KullaniciID=? AND o.IadeEdildiMi=0
            """
            cursor.execute(sql_active, (uid,))
            active = [{"kitap": r[0], "alis": r[1].strftime('%d.%m.%Y %H:%M'), "teslim": r[2].strftime('%d.%m.%Y %H:%M')} for r in cursor.fetchall()]

            # 2. Geçmiş Ödünçler (TEKRARSIZ - GROUP BY EKLENDİ)
            # Mantık: Kitap adına göre grupla, tarihlerin en büyüğünü (MAX) al.
            sql_past = """
            SELECT k.KitapAdi, MAX(o.AlisTarihi) as SonAlis, MAX(o.IadeTarihi) as SonIade
            FROM OduncIslemleri o
            JOIN KitapKopyalari kc ON o.KopyaID=kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID=k.KitapID
            WHERE o.KullaniciID=? AND o.IadeEdildiMi=1
            GROUP BY k.KitapAdi
            ORDER BY SonIade DESC
            """
            cursor.execute(sql_past, (uid,))
            past = [{"kitap": r[0], "alis": r[1].strftime('%d.%m.%Y'), "iade": r[2].strftime('%d.%m.%Y')} for r in cursor.fetchall()]

            # 3. Toplam Borç Hesabı (Aynı kalıyor)
            # A) Kesinleşmiş
            sql_static = "SELECT SUM(c.Tutar) FROM Cezalar c JOIN OduncIslemleri o ON c.OduncID = o.OduncID WHERE o.KullaniciID = ? AND c.OdendiMi = 0"
            cursor.execute(sql_static, (uid,))
            val_static = cursor.fetchone()[0]
            static_debt = float(val_static) if val_static else 0.0

            # B) Canlı
            sql_dynamic = "SELECT SUM(DATEDIFF(minute, SonTeslimTarihi, GETDATE())) FROM OduncIslemleri WHERE KullaniciID = ? AND IadeEdildiMi = 0 AND GETDATE() > SonTeslimTarihi"
            cursor.execute(sql_dynamic, (uid,))
            val_dynamic = cursor.fetchone()[0]
            dynamic_debt = float(val_dynamic) if val_dynamic else 0.0

            total_debt = static_debt + dynamic_debt

            return {
                "active_loans": active, 
                "past_loans": past,
                "total_debt": total_debt
            }
        except Exception as e:
            print(f"Üye Detay Hatası: {e}")
            return {"active_loans": [], "past_loans": [], "total_debt": 0}
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
    # --- CANLI BORÇ HESAPLAMA (ÖĞRENCİ İÇİN) ---
    def get_unpaid_fines(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # UNION ALL kullanarak iki sorguyu birleştiriyoruz:
            # 1. Kısım: Zaten kesilmiş ve veritabanına kaydedilmiş cezalar (Eskiden kalanlar)
            # 2. Kısım: Şu an elinde olan ve süresi geçmiş kitapların ANLIK cezası (Henüz iade edilmemiş)
            
            sql = """
            SELECT c.CezaID, k.KitapAdi, c.Tutar, o.SonTeslimTarihi, 'Kesinleşmiş' as Durum
            FROM Cezalar c
            JOIN OduncIslemleri o ON c.OduncID = o.OduncID
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            WHERE o.KullaniciID = ? AND c.OdendiMi = 0

            UNION ALL

            SELECT 
                0 as CezaID, -- Henüz veritabanında olmadığı için ID'si 0
                k.KitapAdi, 
                DATEDIFF(minute, o.SonTeslimTarihi, GETDATE()) * 1.0 as Tutar, -- Dakika başı 1 TL hesapla
                o.SonTeslimTarihi,
                'Şu An İşliyor' as Durum
            FROM OduncIslemleri o
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            WHERE o.KullaniciID = ? 
              AND o.IadeEdildiMi = 0 
              AND GETDATE() > o.SonTeslimTarihi
            """
            cursor.execute(sql, (user_id, user_id))
            rows = cursor.fetchall()
            
            return [{
                "id": r[0], 
                "kitap": r[1] + (f" ({r[4]})" if r[4] == 'Şu An İşliyor' else ""), # Kitap adının yanına durumu yazalım
                "tutar": float(r[2]), 
                "tarih": r[3].strftime('%d.%m.%Y %H:%M')
            } for r in rows]
        except Exception as e:
            print(e)
            return []
        finally: cursor.close(); conn.close()

    # bu fonksiyon kullanicinin borclarini odemesini saglar
    # --- GÜVENLİ ÖDEME SİSTEMİ (HEM ÖĞRENCİ HEM ADMIN İÇİN GEÇERLİ) ---
    # --- GELİŞMİŞ ÖDEME SİSTEMİ (MESAJLI) ---
    # --- KESİN KİLİTLİ ÖDEME SİSTEMİ (NİHAİ VERSİYON) ---
    def pay_fine(self, user_id, fine_id=None):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. SENARYO: "Tümünü Öde" Butonu
            if fine_id is None:
                # Önce Kontrol: Öğrencinin elinde süresi geçmiş ve henüz iade edilmemiş kitap var mı?
                check_overdue_active = """
                SELECT COUNT(*) FROM OduncIslemleri 
                WHERE KullaniciID = ? AND IadeEdildiMi = 0 AND GETDATE() > SonTeslimTarihi
                """
                cursor.execute(check_overdue_active, (user_id,))
                if cursor.fetchone()[0] > 0:
                    return {"success": False, "message": "Elinizde süresi dolmuş kitaplar var! Önce onları iade etmelisiniz."}

                # Engel yoksa, veritabanındaki (kesinleşmiş) borçları öde
                sql = """
                UPDATE Cezalar 
                SET OdendiMi = 1, OdemeTarihi = GETDATE() 
                WHERE OdendiMi = 0 
                  AND OduncID IN (SELECT OduncID FROM OduncIslemleri WHERE KullaniciID = ?)
                """
                cursor.execute(sql, (user_id,))
                
                # Eğer güncellenen satır yoksa (ama borç görüyorsa, demek ki o borç canlı borçtur)
                if cursor.rowcount == 0:
                     return {"success": False, "message": "Ödenecek kesinleşmiş ceza bulunamadı. (Canlı borçlar iade sonrası ödenir)"}

            # 2. SENARYO: Tekil Ödeme (Listeden "Öde"ye basınca)
            else:
                # KRİTİK KONTROL: Eğer ID 0 geliyorsa, bu "Canlı Ceza"dır.
                if int(fine_id) == 0:
                    return {"success": False, "message": "Bu borç şu an işliyor! Kitabı iade edene kadar ödeyemezsiniz."}

                # Veritabanında kayıtlı bir ceza ise, kitabın durumunu kontrol et
                check_sql = """
                SELECT COUNT(*) FROM Cezalar c
                JOIN OduncIslemleri o ON c.OduncID = o.OduncID
                WHERE c.CezaID = ? AND o.IadeEdildiMi = 0
                """
                cursor.execute(check_sql, (fine_id,))
                if cursor.fetchone()[0] > 0:
                    return {"success": False, "message": "Bu kitabı henüz iade etmediniz! Önce iade, sonra ödeme."}

                # Her şey temizse ödemeyi yap
                sql = "UPDATE Cezalar SET OdendiMi = 1, OdemeTarihi = GETDATE() WHERE CezaID = ?"
                cursor.execute(sql, (fine_id,))
            
            conn.commit()
            return {"success": True, "message": "Ödeme başarıyla alındı."}
        except Exception as e:
            print(f"Ödeme Hatası: {e}")
            return {"success": False, "message": "Sistem hatası oluştu."}
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
    # --- CANLI BORÇ HESAPLAMA (ADMİN İÇİN) ---
    def get_all_unpaid_fines_admin(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # Yine aynı mantık: Veritabanındaki cezalar + Şu an işleyen canlı cezalar
            sql = """
            SELECT u.Ad + ' ' + u.Soyad as Uye, k.KitapAdi, o.SonTeslimTarihi, c.Tutar, 'Kesinleşmiş' as Tip
            FROM Cezalar c
            JOIN OduncIslemleri o ON c.OduncID = o.OduncID
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            JOIN Kullanicilar u ON o.KullaniciID = u.KullaniciID
            WHERE c.OdendiMi = 0

            UNION ALL

            SELECT 
                u.Ad + ' ' + u.Soyad as Uye,
                k.KitapAdi,
                o.SonTeslimTarihi,
                DATEDIFF(minute, o.SonTeslimTarihi, GETDATE()) * 1.0 as Tutar,
                'Şu An İşliyor' as Tip
            FROM OduncIslemleri o
            JOIN KitapKopyalari kc ON o.KopyaID = kc.KopyaID
            JOIN Kitaplar k ON kc.KitapID = k.KitapID
            JOIN Kullanicilar u ON o.KullaniciID = u.KullaniciID
            WHERE o.IadeEdildiMi = 0 
              AND GETDATE() > o.SonTeslimTarihi
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            fines = []
            for r in rows:
                fines.append({
                    "uye": r[0], 
                    "kitap": r[1] + (f" (Canlı - {int(r[3])} dk)" if r[4] == 'Şu An İşliyor' else ""), 
                    "tarih": r[2].strftime('%d.%m.%Y %H:%M') if r[2] else "-", 
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
            # Trigger olduğu için sadece Müsait (DurumID=1 veya 'Musait') olanı seçmemiz yeterli
            cursor.execute("""
                SELECT TOP 1 kc.KopyaID 
                FROM KitapKopyalari kc
                JOIN Kitaplar k ON kc.KitapID = k.KitapID
                WHERE k.ISBN = ? AND (kc.Durum = 'Musait' OR kc.DurumID = 1)
            """, (isbn,))
            
            copy = cursor.fetchone()
            if not copy: return {"success": False, "message": "Bu kitabın müsait kopyası yok!"}
            copy_id = copy[0]

            # 3. Ödünç işlemini kaydet
            # DİKKAT: Artık SonTeslimTarihi'ni hesaplamıyoruz.
            # Veritabanına şimdiki zamanı gönderiyoruz, Trigger onu hemen 1 dk sonrasına güncelleyecek.
            now = datetime.now()
            
            sql = "INSERT INTO OduncIslemleri (KopyaID, KullaniciID, AlisTarihi, SonTeslimTarihi, IadeEdildiMi) VALUES (?, ?, ?, ?, 0)"
            cursor.execute(sql, (copy_id, user_id, now, now)) 
            
            # --- BURADAKİ UPDATE KODLARINI SİLDİK ---
            # Çünkü SQL Trigger (trg_OduncBaslat) artık kitap durumunu otomatik 'Oduncte' yapıyor.
            
            conn.commit()
            return {"success": True, "message": "Ödünç verme başarılı! (Süre: 1 Dakika)"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            cursor.close(); conn.close()