from src.utils.db import db

def fix_requests_final():
    print("⏳ Talep tablosu baştan aşağı onarılıyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Eski (bozuk) tabloyu sil
        print("🗑️ Eski tablo siliniyor...")
        cursor.execute("IF OBJECT_ID('KitapIstekleri', 'U') IS NOT NULL DROP TABLE KitapIstekleri")
        conn.commit()

        # 2. Yeni (doğru) tabloyu oluştur - TalepTarihi İLE!
        print("🔨 Yeni tablo oluşturuluyor (TalepTarihi sütunuyla)...")
        sql = """
        CREATE TABLE KitapIstekleri (
            IstekID INT PRIMARY KEY IDENTITY(1,1),
            KullaniciID INT NOT NULL,
            KitapID INT NOT NULL,
            TalepTarihi DATETIME DEFAULT GETDATE(), -- İşte eksik olan sütun buydu!
            Durum NVARCHAR(20) DEFAULT 'Bekliyor',
            FOREIGN KEY (KullaniciID) REFERENCES Kullanicilar(KullaniciID),
            FOREIGN KEY (KitapID) REFERENCES Kitaplar(KitapID)
        )
        """
        cursor.execute(sql)
        conn.commit()
        print("✅ Tablo yapısı düzeltildi.")

        # 3. Test için hemen içine bir talep atalım (Admin paneli boş kalmasın)
        print("🌱 Test verisi ekleniyor...")
        
        # İlk kullanıcıyı ve kitabı bul
        cursor.execute("SELECT TOP 1 KullaniciID FROM Kullanicilar")
        user = cursor.fetchone()
        cursor.execute("SELECT TOP 1 KitapID FROM Kitaplar")
        book = cursor.fetchone()

        if user and book:
            # Sahte talep ekle
            cursor.execute("INSERT INTO KitapIstekleri (KullaniciID, KitapID, Durum) VALUES (?, ?, 'Bekliyor')", (user[0], book[0]))
            conn.commit()
            print("✅ Test talebi başarıyla eklendi!")
        else:
            print("⚠️ Veritabanında hiç üye veya kitap olmadığı için test verisi eklenemedi.")

    except Exception as e:
        print(f"❌ HATA: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_requests_final()