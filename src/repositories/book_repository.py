from src.utils.db import db

class BookRepository:
    
    # --- 1. KİTAPLARI SAYFALI GETİR ---
    def get_books_paginated(self, page, per_page=8):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            offset = (page - 1) * per_page
            # Ozet yerine Aciklama sütununu kullanıyoruz (Hata almamak için)
            sql = """
            SELECT k.KitapID, k.ISBN, k.KitapAdi, k.YayinYili, y.Ad as Yayinevi, k.ResimURL, k.SayfaSayisi, k.Aciklama
            FROM Kitaplar k
            LEFT JOIN Yayinevleri y ON k.YayineviID = y.YayineviID
            ORDER BY k.KitapID DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(sql, (offset, per_page))
            rows = cursor.fetchall()
            books = []
            for row in rows:
                books.append({
                    "id": row.KitapID, "isbn": row.ISBN, "ad": row.KitapAdi,
                    "yil": row.YayinYili, "yayinevi": row.Yayinevi, "resim": row.ResimURL,
                    "sayfa": row.SayfaSayisi, "aciklama": row.Aciklama
                })
            return books
        except Exception as e:
            print(f"Hata: {e}")
            return []
        finally: cursor.close(); conn.close()

    # --- 2. YORUMLARI GETİR ---
# --- 2. YORUMLARI GETİR (ESKİSİNİ SİLİP BUNU YAPIŞTIR) ---
    def get_comments(self, book_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # YorumID ve KullaniciID bilgisini de çekiyoruz (Silme işlemi için şart!)
            sql = """
            SELECT y.YorumID, y.KullaniciID, y.YorumMetni, y.YorumTarihi, u.Ad + ' ' + u.Soyad as Kisi, u.Avatar
            FROM KitapYorumlari y
            JOIN Kullanicilar u ON y.KullaniciID = u.KullaniciID
            WHERE y.KitapID = ?
            ORDER BY y.YorumTarihi DESC
            """
            cursor.execute(sql, (book_id,))
            rows = cursor.fetchall()
            
            return [{
                "id": row.YorumID,          # <--- Bu satır YENİ (Silmek için lazım)
                "user_id": row.KullaniciID, # <--- Bu satır YENİ (Kimlik kontrolü için)
                "yorum": row.YorumMetni,
                "tarih": row.YorumTarihi.strftime('%d.%m.%Y'),
                "kisi": row.Kisi,
                "avatar": row.Avatar if hasattr(row, 'Avatar') else 'avatar1'
            } for row in rows]

        except Exception as e:
            print(f"❌ YORUM GETİRME HATASI: {e}")
            return [] 
        finally: cursor.close(); conn.close()

    # --- YENİ: YORUM SİL (BUNU DİREKT EKLE) ---
    def delete_comment(self, comment_id, user_id, role):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # EĞER ADMİNSE (Rol 1 veya 2): Her şeyi silebilir.
            if role != 3: 
                sql = "DELETE FROM KitapYorumlari WHERE YorumID = ?"
                cursor.execute(sql, (comment_id,))
            
            # EĞER ÖĞRENCİYSE (Rol 3): Sadece kendi yorumunu silebilir.
            else:
                sql = "DELETE FROM KitapYorumlari WHERE YorumID = ? AND KullaniciID = ?"
                cursor.execute(sql, (comment_id, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return {"success": True, "message": "Yorum silindi."}
            else:
                return {"success": False, "message": "Bu işlem için yetkiniz yok veya yorum bulunamadı."}

        except Exception as e:
            return {"success": False, "message": str(e)}
        finally: cursor.close(); conn.close()

    # --- 3. YORUM EKLE ---
    def add_comment(self, user_id, book_id, text):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO KitapYorumlari (KullaniciID, KitapID, YorumMetni) VALUES (?, ?, ?)"
            cursor.execute(sql, (user_id, book_id, text))
            conn.commit()
            return True
        except Exception as e:
            print(f"Yorum Hata: {e}")
            return False
        finally: cursor.close(); conn.close()

    # --- 4. TALEP ET (ÖĞRENCİ) - [GERİ EKLENDİ] ---
    def request_book(self, user_id, book_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # Önce kontrol: Zaten bekleyen isteği var mı?
            check = "SELECT Count(*) FROM KitapIstekleri WHERE KullaniciID=? AND KitapID=? AND Durum='Bekliyor'"
            cursor.execute(check, (user_id, book_id))
            if cursor.fetchone()[0] > 0:
                return {"success": False, "message": "Zaten bu kitap için bekleyen talebin var!"}

            sql = "INSERT INTO KitapIstekleri (KullaniciID, KitapID) VALUES (?, ?)"
            cursor.execute(sql, (user_id, book_id))
            conn.commit()
            return {"success": True, "message": "Talep iletildi! Admin onayı bekleniyor."}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally: cursor.close(); conn.close()

    # --- 5. TALEPLERİ GÖR (ADMİN) - [GERİ EKLENDİ] ---
    def get_pending_requests(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            SELECT i.IstekID, k.KitapAdi, u.Ad + ' ' + u.Soyad as Ogrenci, i.TalepTarihi, k.ResimURL
            FROM KitapIstekleri i
            JOIN Kitaplar k ON i.KitapID = k.KitapID
            JOIN Kullanicilar u ON i.KullaniciID = u.KullaniciID
            WHERE i.Durum = 'Bekliyor'
            ORDER BY i.TalepTarihi DESC
            """
            cursor.execute(sql)
            return [{"id": r.IstekID, "kitap": r.KitapAdi, "ogrenci": r.Ogrenci, "tarih": r.TalepTarihi.strftime('%d.%m.%Y'), "resim": r.ResimURL} for r in cursor.fetchall()]
        except: return []
        finally: cursor.close(); conn.close()

    # --- 6. TALEBİ İŞLE (ADMİN) - [GERİ EKLENDİ] ---
    def process_request(self, request_id, action):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            if action == 'reject':
                cursor.execute("UPDATE KitapIstekleri SET Durum='Reddedildi' WHERE IstekID=?", (request_id,))
                conn.commit()
                return {"success": True, "message": "Talep reddedildi."}

            if action == 'approve':
                # İsteği bul
                cursor.execute("SELECT KullaniciID, KitapID FROM KitapIstekleri WHERE IstekID=?", (request_id,))
                req = cursor.fetchone()
                if not req: return {"success": False, "message": "İstek bulunamadı."}
                
                # Müsait kopya bul
                cursor.execute("SELECT TOP 1 KopyaID FROM KitapKopyalari WHERE KitapID=? AND Durum='Musait'", (req.KitapID,))
                copy = cursor.fetchone()
                if not copy: return {"success": False, "message": "Stokta müsait kitap yok!"}

                # Ödünç ver
                import datetime
                now = datetime.datetime.now()
                due = now + datetime.timedelta(days=15)
                cursor.execute("INSERT INTO OduncIslemleri (KopyaID, KullaniciID, AlisTarihi, SonTeslimTarihi) VALUES (?, ?, ?, ?)", (copy.KopyaID, req.KullaniciID, now, due))
                cursor.execute("UPDATE KitapKopyalari SET Durum='Oduncte' WHERE KopyaID=?", (copy.KopyaID,))
                cursor.execute("UPDATE KitapIstekleri SET Durum='Onaylandi' WHERE IstekID=?", (request_id,))
                conn.commit()
                return {"success": True, "message": "Kitap öğrenciye verildi!"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally: cursor.close(); conn.close()

    # --- 7. TÜM KİTAPLAR (SAYI İÇİN) - [GERİ EKLENDİ] ---
    def get_all_books(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT KitapID FROM Kitaplar")
            return cursor.fetchall() # Sadece sayısını almak için tüm listeyi dönüyoruz
        except: return []
        finally: cursor.close(); conn.close()

    # --- 8. ARAMA VE EKLEME ---
    def search_books(self, term):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT KitapID, KitapAdi, ISBN, ResimURL, YayinYili, Aciklama FROM Kitaplar WHERE KitapAdi LIKE ?"
            cursor.execute(sql, (f"%{term}%",))
            rows = cursor.fetchall()
            return [{"id":r.KitapID, "ad":r.KitapAdi, "isbn":r.ISBN, "resim":r.ResimURL, "yil":r.YayinYili, "aciklama":r.Aciklama} for r in rows]
        except: return []
        finally: cursor.close(); conn.close()

    def add_book(self, data):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO Kitaplar (KitapAdi, ISBN, YayinYili, SayfaSayisi, YayineviID, Dil, Aciklama, ResimURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(sql, (data['baslik'], data['isbn'], data['yayin_yili'], data['sayfa'], data['yayinevi_id'], data['dil'], data['aciklama'], data.get('resim_url')))
            conn.commit()
            return True
        except: return False
        finally: cursor.close(); conn.close()
        
    def add_book_copy(self, k, b, r): return True
    def delete_book(self, i): return True

# ... (Mevcut kodların altına ekle) ...

    # --- 9. FAVORİ İŞLEMLERİ ---
    def toggle_favorite(self, user_id, book_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # Önce var mı diye bak
            check = "SELECT FavoriID FROM FavoriKitaplar WHERE KullaniciID=? AND KitapID=?"
            cursor.execute(check, (user_id, book_id))
            row = cursor.fetchone()
            
            if row:
                # Varsa SİL (Favoriden çıkar)
                cursor.execute("DELETE FROM FavoriKitaplar WHERE FavoriID=?", (row[0],))
                conn.commit()
                return {"success": True, "status": "removed", "message": "Favorilerden çıkarıldı."}
            else:
                # Yoksa EKLE (Favoriye al)
                cursor.execute("INSERT INTO FavoriKitaplar (KullaniciID, KitapID) VALUES (?, ?)", (user_id, book_id))
                conn.commit()
                return {"success": True, "status": "added", "message": "Favorilere eklendi!"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally: cursor.close(); conn.close()

    def get_user_favorites(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # Favori kitapların detaylarını getir
            sql = """
            SELECT k.KitapID, k.KitapAdi, k.ResimURL, y.Ad as Yayinevi, k.ISBN, k.Aciklama
            FROM FavoriKitaplar f
            JOIN Kitaplar k ON f.KitapID = k.KitapID
            LEFT JOIN Yayinevleri y ON k.YayineviID = y.YayineviID
            WHERE f.KullaniciID = ?
            ORDER BY f.EklemeTarihi DESC
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return [{"id": r.KitapID, "ad": r.KitapAdi, "resim": r.ResimURL, "yayinevi": r.Yayinevi, "isbn":r.ISBN, "aciklama":r.Aciklama} for r in rows]
        except: return []
        finally: cursor.close(); conn.close()

    def get_favorite_ids(self, user_id):
        # Sadece ID listesi döner (Kalpleri boyamak için)
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT KitapID FROM FavoriKitaplar WHERE KullaniciID=?", (user_id,))
            return [row[0] for row in cursor.fetchall()]
        except: return []
        finally: cursor.close(); conn.close()