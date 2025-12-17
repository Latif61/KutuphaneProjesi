from src.utils.db import db

def create_favorites_table():
    print("⏳ Favori tablosu oluşturuluyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FavoriKitaplar' AND xtype='U')
        CREATE TABLE FavoriKitaplar (
            FavoriID INT PRIMARY KEY IDENTITY(1,1),
            KullaniciID INT NOT NULL,
            KitapID INT NOT NULL,
            EklemeTarihi DATETIME DEFAULT GETDATE(),
            FOREIGN KEY (KullaniciID) REFERENCES Kullanicilar(KullaniciID),
            FOREIGN KEY (KitapID) REFERENCES Kitaplar(KitapID),
            CONSTRAINT UQ_User_Book UNIQUE(KullaniciID, KitapID) -- Aynı kitabı 2 kere favorileyemesin
        )
        """
        cursor.execute(sql)
        conn.commit()
        print("✅ BAŞARILI: 'FavoriKitaplar' tablosu hazır.")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        cursor.close(); conn.close()

if __name__ == "__main__":
    create_favorites_table()