from src.utils.db import db
import datetime

class BookRepository:
    
    # controllerdan gelen sayfa numarasina gore kitaplari sayfa sayfa getirir
    def get_books_paginated(self, page, per_page=8): 
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            offset = (page - 1) * per_page # hangi sayfadaysak ona gore kitaplari atlar 8 tanesini getirir
            sql = """
            SELECT k.KitapID, k.ISBN, k.KitapAdi, k.Yazar, k.YayinYili, 
                   y.Ad as Yayinevi, cat.KategoriAd, k.ResimURL, k.SayfaSayisi, k.Aciklama, k.KategoriID,
                   (SELECT COUNT(*) FROM KitapKopyalari WHERE KitapID = k.KitapID) as ToplamKopya,
                   (SELECT COUNT(*) FROM KitapKopyalari WHERE KitapID = k.KitapID AND DurumID = 1) as MusaitKopya
            FROM Kitaplar k
            LEFT JOIN Yayinevleri y ON k.YayineviID = y.YayineviID
            LEFT JOIN KitapKategorileri cat ON k.KategoriID = cat.KategoriID
            ORDER BY k.KitapID DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(sql, (offset, per_page))
            rows = cursor.fetchall()
            
            books = []
            for r in rows:
                books.append({ # veritabanindan gelen ham veriyi burada duzenleyip frontende gonderiyoruz
                    "id": r[0], "isbn": r[1], "ad": r[2], "yazar": r[3], "yil": r[4],
                    "yayinevi": r[5], "kategori": r[6] if r[6] else "Genel", 
                    "resim": r[7], "sayfa": r[8], "aciklama": r[9], "kategori_id": r[10],
                    "toplam": r[11], 
                    "musait": r[12]  
                })
            return books 
        except Exception as e:
            print(f"❌ Kitap Listeleme Hatası: {e}")
            return []
        finally:
            cursor.close(); conn.close()

    # bu fonksiyon controllerdan gelen kelimeye gore kitaplari arar ve getirir
    # sql'deki where komutu sayesinde ayni anda kitap adi, yazar adi veya isbn numarasina gore arama yapabilir
    def search_books(self, query):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            search_pattern = f"%{query}%" # % isareti sayesinde kullanici Harry bile yazsa icinde Harry gecen tum kitaplari getirir(query : kullanicidan yazdigi kelime)
            sql = """
            SELECT k.KitapID, k.ISBN, k.KitapAdi, k.Yazar, k.YayinYili, 
                   y.Ad as Yayinevi, cat.KategoriAd, k.ResimURL, k.SayfaSayisi, k.Aciklama, k.KategoriID,
                   (SELECT COUNT(*) FROM KitapKopyalari WHERE KitapID = k.KitapID) as ToplamKopya,
                   (SELECT COUNT(*) FROM KitapKopyalari WHERE KitapID = k.KitapID AND DurumID = 1) as MusaitKopya
            FROM Kitaplar k
            LEFT JOIN Yayinevleri y ON k.YayineviID = y.YayineviID
            LEFT JOIN KitapKategorileri cat ON k.KategoriID = cat.KategoriID
            WHERE k.KitapAdi LIKE ? OR k.Yazar LIKE ? OR k.ISBN LIKE ? 
            """
            cursor.execute(sql, (search_pattern, search_pattern, search_pattern))
            rows = cursor.fetchall()
            
            books = []
            for r in rows:
                books.append({ # veritabanindan gelen ham veriyi burada duzenleyip frontende gonderiyoruz
                    "id": r[0], "isbn": r[1], "ad": r[2], "yazar": r[3], "yil": r[4],
                    "yayinevi": r[5], "kategori": r[6] if r[6] else "Genel",
                    "resim": r[7], "sayfa": r[8], "aciklama": r[9], "kategori_id": r[10],
                    "toplam": r[11], 
                    "musait": r[12]
                })
            return books # arama sonucu bulunan kitaplari dondurur
        except Exception as e:
            print(f"❌ Arama Hatası: {e}")
            return []
        finally:
            cursor.close(); conn.close()

    # controllerdan gelen kitap id'sine gore o kitabin yorumlarini getirir
    def get_comments(self, book_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:# sql sayfasina gitmesinin sebebi burada sadece yorumu cekmiyoruz yorumu yazan kisinin de bilgisini cekiyoruz
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
                "id": row[0],
                "user_id": row[1],
                "yorum": row[2],
                "tarih": row[3].strftime('%d.%m.%Y') if row[3] else '',
                "kisi": row[4],
                "avatar": row[5] if row[5] else 'avatar1'
            } for row in rows]
        except Exception as e:
            print(f"❌ YORUM GETİRME HATASI: {e}")
            return [] 
        finally: cursor.close(); conn.close()

    # bu fonksiyon controllerdan gelen yorum id'sine ve user id'sine gore yorum silme islemini yapar
    def delete_comment(self, comment_id, user_id, role):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            if int(role) != 3: # Admin ise her seyi siler
                sql = "DELETE FROM KitapYorumlari WHERE YorumID = ?"
                cursor.execute(sql, (comment_id,))
            else: # Öğrenci ise sadece kendi yorumunu siler
                sql = "DELETE FROM KitapYorumlari WHERE YorumID = ? AND KullaniciID = ?"
                cursor.execute(sql, (comment_id, user_id))
            
            if cursor.rowcount > 0: # etkilenen satir sayisi 0'dan buyukse silme islemi basarili demektir
                conn.commit()
                return {"success": True, "message": "Yorum silindi."}
            return {"success": False, "message": "Yorum bulunamadı veya yetkiniz yok."}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally: cursor.close(); conn.close()

    # controllerdan gelen kullanici id'si, kitap id'si ve yorum metni bilgilerini alir ve yorumlar kismina ekler veritabanina kaydeder
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

    # bu fonksiyon controllerdan gelen bilgilere gore kullanicinin kitap talep etmesini saglar
    def request_book(self, user_id, book_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            check = "SELECT Count(*) FROM KitapIstekleri WHERE KullaniciID=? AND KitapID=? AND Durum='Bekliyor'"
            cursor.execute(check, (user_id, book_id)) # kullanicinin zaten o kitap icin bekleyen bir talebi var mi kontrol eder
            if cursor.fetchone()[0] > 0:
                return {"success": False, "message": "Zaten bu kitap için bekleyen talebin var!"}

            sql = "INSERT INTO KitapIstekleri (KullaniciID, KitapID) VALUES (?, ?)"
            cursor.execute(sql, (user_id, book_id))
            conn.commit()
            return {"success": True, "message": "Talep iletildi! Admin onayı bekleniyor."}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally: cursor.close(); conn.close()

    # bu fonksiyon yoneticinin bekleyen kitap taleplerini listelemesini saglar
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

    # bu fonksiyon controllerdan gelen istek id'sine gore o istegi onaylar veya reddeder
    def process_request(self, request_id, action):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            if action == 'reject': # istegi reddeder
                cursor.execute("UPDATE KitapIstekleri SET Durum='Reddedildi' WHERE IstekID=?", (request_id,))
                conn.commit()
                return {"success": True, "message": "Talep reddedildi."}

            if action == 'approve':
                # istegi onaylar ve kitabi kullaniciya odunc verir
                cursor.execute("SELECT KullaniciID, KitapID FROM KitapIstekleri WHERE IstekID=?", (request_id,))
                req = cursor.fetchone()
                if not req: return {"success": False, "message": "İstek bulunamadı."}
                # uygun bir kitap kopyasi bulur
                cursor.execute("SELECT TOP 1 KopyaID FROM KitapKopyalari WHERE KitapID=? AND (DurumID=1 OR Durum='Musait')", (req.KitapID,))
                copy = cursor.fetchone()
                if not copy: return {"success": False, "message": "Stokta müsait kitap yok!"}
                # kitap kopyasinin durumunu 'odunc verildi' olarak günceller
                now = datetime.datetime.now()
                cursor.execute("INSERT INTO OduncIslemleri (KopyaID, KullaniciID, AlisTarihi, SonTeslimTarihi) VALUES (?, ?, ?, ?)", (copy.KopyaID, req.KullaniciID, now, now))
                # kitap kopyasinin durumunu gunceller
                cursor.execute("UPDATE KitapIstekleri SET Durum='Onaylandi' WHERE IstekID=?", (request_id,))
                conn.commit()
                return {"success": True, "message": "Kitap onaylandı ve ödünç verildi! (Süre: 1 dk)"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally: cursor.close(); conn.close()

    # bu fonksiyon controllerdan gelen kitap bilgilerini alir ve veritabanina yeni kitap olarak ekler
    def add_book(self, data):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO Kitaplar (KitapAdi, Yazar, ISBN, YayinYili, SayfaSayisi, YayineviID, Dil, Aciklama, ResimURL, KategoriID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(sql, (data['baslik'], data['yazar'], data['isbn'], data['yayin_yili'], data['sayfa'], data['yayinevi_id'], data['dil'], data['aciklama'], data.get('resim_url'), data.get('kategori_id')))
            conn.commit()
            return True
        except Exception as e:
            print(f"Kitap Ekleme Hatası: {e}")
            return False
        finally: cursor.close(); conn.close()

    # bu fonksiyon controllerdan gelen kitap id'sine ve guncel verilerine gore o kitabi gunceller
    def update_book(self, book_id, data):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            UPDATE Kitaplar 
            SET KitapAdi = ?, Yazar = ?, ISBN = ?, YayinYili = ?, 
                SayfaSayisi = ?, YayineviID = ?, Aciklama = ?, ResimURL = ?, KategoriID = ?
            WHERE KitapID = ?
            """
            cursor.execute(sql, (
                data['baslik'], data['yazar'], data['isbn'], data['yayin_yili'],
                data['sayfa'], data['yayinevi_id'], data['aciklama'], 
                data.get('resim_url'), data.get('kategori_id'), book_id
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Güncelleme Hatası: {e}")
            return False
        finally: cursor.close(); conn.close()

    # bu fonksiyon controllerdan gelen kitap id'sine gore o kitabi veritabanindan siler ve zincirleme silme islemi yapar
    def delete_book(self, book_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM KitapIstekleri WHERE KitapID = ?", (book_id,))
            cursor.execute("DELETE FROM FavoriKitaplar WHERE KitapID = ?", (book_id,))
            cursor.execute("DELETE FROM KitapYorumlari WHERE KitapID = ?", (book_id,))
            cursor.execute("DELETE FROM OduncIslemleri WHERE KopyaID IN (SELECT KopyaID FROM KitapKopyalari WHERE KitapID = ?)", (book_id,))
            cursor.execute("DELETE FROM KitapKopyalari WHERE KitapID = ?", (book_id,))
            cursor.execute("DELETE FROM Kitaplar WHERE KitapID = ?", (book_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Kitap Silme Hatası: {e}")
            conn.rollback()
            return False
        finally: cursor.close(); conn.close()

    # bu fonksiyon controllerdan gelen kullanici id'si ve kitap id'sine gore 
    # kullanicinin o kitabi favorilere ekleyip eklemedigini kontrol eder ve ekleme veya cikarma islemini de yapar
    def toggle_favorite(self, user_id, book_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            check = "SELECT FavoriID FROM FavoriKitaplar WHERE KullaniciID=? AND KitapID=?"
            cursor.execute(check, (user_id, book_id))
            row = cursor.fetchone() # bu satirda kullanicinin o kitabi favorilere ekleyip eklemedigini kontrol ediyoruz row degiskeni varsa o zaman o kitabi favorilere eklemis demektir
            if row:
                cursor.execute("DELETE FROM FavoriKitaplar WHERE FavoriID=?", (row[0],)) # eger kitap favorilerdeyse cikarma islemi yapar
                conn.commit()
                return {"success": True, "status": "removed"}
            else:
                cursor.execute("INSERT INTO FavoriKitaplar (KullaniciID, KitapID) VALUES (?, ?)", (user_id, book_id)) # eger kitap favorilerde degilse ekleme islemi yapar
                conn.commit()
                return {"success": True, "status": "added"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally: cursor.close(); conn.close()

   # contollerdan gelen kullanici id'sine gore o kullanicinin favori kitaplarini getirir
   # burada onemli olan sadece id almasina ragmen join islemi yaparak kitap adi, resim vs. bilgilerini de aliyoruz
    def get_user_favorites(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            SELECT k.KitapID, k.KitapAdi, k.ResimURL, y.Ad as Yayinevi, k.ISBN, k.Aciklama
            FROM FavoriKitaplar f
            JOIN Kitaplar k ON f.KitapID = k.KitapID
            LEFT JOIN Yayinevleri y ON k.YayineviID = y.YayineviID
            WHERE f.KullaniciID = ? ORDER BY f.EklemeTarihi DESC
            """
            cursor.execute(sql, (user_id,))
            return [{"id": r.KitapID, "ad": r.KitapAdi, "resim": r.ResimURL, "yayinevi": r.Yayinevi, "isbn":r.ISBN, "aciklama":r.Aciklama} for r in cursor.fetchall()]
        except: return []
        finally: cursor.close(); conn.close()

    # controllerdan gelen kullanici id'sine gore o kullanicinin favori kitaplarinin sadece id'lerini getirir
    # neden var cunku ana sayfa icin bir kitabin favori olup olmadigini anlamak icin en kolay id'si ile anlariz diger verileri cekip yuk olmaya gerek yok
    def get_favorite_ids(self, user_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT KitapID FROM FavoriKitaplar WHERE KullaniciID=?", (user_id,))
            return [row[0] for row in cursor.fetchall()]
        except: return []
        finally: cursor.close(); conn.close()

    # kutuphanedeki kitap kategorilerini getirir
    def get_all_categories(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT KategoriID, KategoriAd FROM KitapKategorileri")
            return [{"id": int(r[0]), "ad": str(r[1])} for r in cursor.fetchall()]
        except: return []
        finally: cursor.close(); conn.close()

    # bu fonksiyon controllerdan gelen kitap bilgilerini alir ve veritabanina yeni kitap kopyasi olarak ekler
    def add_book_copy(self, data):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO KitapKopyalari (KitapID, Barkod, RafKonumu, DurumID) VALUES (?, ?, ?, 1)"
            cursor.execute(sql, (data['kitap_id'], data['barkod'], data['raf_konumu']))
            conn.commit()
            return True
        except: return False
        finally: cursor.close(); conn.close()

    # bu fonksiyon kütüphanedeki kitaplarin turlerine gore dagilimini hesaplar
    def get_category_distribution(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
            SELECT cat.KategoriAd, COUNT(k.KitapID) as KitapSayisi
            FROM Kitaplar k
            INNER JOIN KitapKategorileri cat ON k.KategoriID = cat.KategoriID
            GROUP BY cat.KategoriAd
            """
            cursor.execute(sql)
            return [{"kategori": r[0], "adet": r[1]} for r in cursor.fetchall()]
        except: return []
        finally: cursor.close(); conn.close()