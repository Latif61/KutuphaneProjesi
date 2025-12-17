from src.utils.db import db
import random

def seed_database():
    print("⏳ Sabit veriler yükleniyor...")
    
    conn = db.get_connection()
    cursor = conn.cursor()

    try:
        # YAYINEVLERİ
        yayinevleri = ["Yapı Kredi Yayınları", "Can Yayınları", "İş Bankası Kültür Yayınları", "İletişim Yayınları", "Doğan Kitap", "İthaki Yayınları"]
        yayinevi_idleri = {}

        for yadi in yayinevleri:
            cursor.execute("SELECT YayineviID FROM Yayinevleri WHERE Ad = ?", (yadi,))
            row = cursor.fetchone()
            if row:
                yayinevi_idleri[yadi] = row[0]
            else:
                cursor.execute("INSERT INTO Yayinevleri (Ad) VALUES (?)", (yadi,))
                conn.commit()
                cursor.execute("SELECT YayineviID FROM Yayinevleri WHERE Ad = ?", (yadi,))
                yayinevi_idleri[yadi] = cursor.fetchone()[0]

        # KİTAPLAR (Resim Linkleri Elle Kontrol Edildi)
        kitaplar = [
            {
                "ad": "Kürk Mantolu Madonna", "isbn": "9789753638029", "yil": 1943, "sayfa": 160, 
                "yayinevi": "Yapı Kredi Yayınları", "yazar": "Sabahattin Ali",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000064052_1.jpg"
            },
            {
                "ad": "1984", "isbn": "9789750718533", "yil": 1949, "sayfa": 352, 
                "yayinevi": "Can Yayınları", "yazar": "George Orwell",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000064038_1.jpg"
            },
            {
                "ad": "Şeker Portakalı", "isbn": "9789750738609", "yil": 1968, "sayfa": 182, 
                "yayinevi": "Can Yayınları", "yazar": "Jose Mauro de Vasconcelos",
                "img": "https://i.dr.com.tr/cache/600x600/0/0001828828001_1.jpg"
            },
            {
                "ad": "Harry Potter ve Felsefe Taşı", "isbn": "9789750802942", "yil": 2001, "sayfa": 276, 
                "yayinevi": "Yapı Kredi Yayınları", "yazar": "J.K. Rowling",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000052675_1.jpg"
            },
            {
                "ad": "Simyacı", "isbn": "9789750726439", "yil": 1988, "sayfa": 188, 
                "yayinevi": "Can Yayınları", "yazar": "Paulo Coelho",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000064043_1.jpg"
            },
            {
                "ad": "Dönüşüm", "isbn": "9786053609403", "yil": 1915, "sayfa": 80, 
                "yayinevi": "İş Bankası Kültür Yayınları", "yazar": "Franz Kafka",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000562308_1.jpg"
            },
            {
                "ad": "Suç ve Ceza", "isbn": "9789750719387", "yil": 1866, "sayfa": 687, 
                "yayinevi": "İş Bankası Kültür Yayınları", "yazar": "Fyodor Dostoyevski",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000064103_1.jpg"
            },
            {
                "ad": "Fahrenheit 451", "isbn": "9786053757818", "yil": 1953, "sayfa": 208, 
                "yayinevi": "İthaki Yayınları", "yazar": "Ray Bradbury",
                "img": "https://i.dr.com.tr/cache/600x600/0/0001764658001_1.jpg"
            },
            {
                "ad": "Satranç", "isbn": "9786053606112", "yil": 1943, "sayfa": 84, 
                "yayinevi": "İş Bankası Kültür Yayınları", "yazar": "Stefan Zweig",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000411497_1.jpg"
            },
            {
                "ad": "Martin Eden", "isbn": "9786053608833", "yil": 1909, "sayfa": 520, 
                "yayinevi": "İş Bankası Kültür Yayınları", "yazar": "Jack London",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000572718_1.jpg"
            },
            {
                "ad": "Sefiller", "isbn": "9786053325686", "yil": 1862, "sayfa": 1724, 
                "yayinevi": "İş Bankası Kültür Yayınları", "yazar": "Victor Hugo",
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000609358_1.jpg"
            },
             {
                "ad": "Uçurtma Avcısı", "isbn": "9789752891456", "yil": 2003, "sayfa": 375, 
                "yayinevi": "Doğan Kitap", "yazar": "Khaled Hosseini", 
                "img": "https://i.dr.com.tr/cache/600x600/0/0000000064434_1.jpg"
            }
        ]

        eklenen = 0
        for b in kitaplar:
            # Kitap var mı?
            cursor.execute("SELECT KitapID FROM Kitaplar WHERE ISBN = ?", (b['isbn'],))
            row = cursor.fetchone()
            
            if row:
                # Sadece resmini güncelle
                cursor.execute("UPDATE Kitaplar SET ResimURL = ? WHERE KitapID = ?", (b['img'], row[0]))
                conn.commit()
            else:
                # Ekle
                y_id = yayinevi_idleri.get(b['yayinevi'], 1)
                sql = """INSERT INTO Kitaplar (KitapAdi, ISBN, YayinYili, SayfaSayisi, YayineviID, Dil, Aciklama, ResimURL)
                         VALUES (?, ?, ?, ?, ?, 'Türkçe', ?, ?)"""
                aciklama = f"{b['yazar']} tarafından yazılan klasik eser."
                cursor.execute(sql, (b['ad'], b['isbn'], b['yil'], b['sayfa'], y_id, aciklama, b['img']))
                conn.commit()
                
                # Kopyalar
                cursor.execute("SELECT KitapID FROM Kitaplar WHERE ISBN = ?", (b['isbn'],))
                kid = cursor.fetchone()[0]
                for i in range(2):
                    barkod = f"BR-{kid}-{random.randint(100,999)}"
                    raf = f"R-{random.randint(1,5)}-{random.randint(1,10)}"
                    cursor.execute("INSERT INTO KitapKopyalari (KitapID, Barkod, Durum, RafKonumu) VALUES (?, ?, 'Musait', ?)", (kid, barkod, raf))
                    conn.commit()
                eklenen += 1

        print(f"🎉 İşlem Bitti! {eklenen} yeni kitap eklendi, diğerlerinin resimleri güncellendi.")

    except Exception as e:
        print(f"❌ HATA: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_database()