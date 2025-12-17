from src.utils.db import db

def create_wishlist_table():
    print("⏳ Favoriler tablosu oluşturuluyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='KitapFavoriler' AND xtype='U')
        CREATE TABLE KitapFavoriler (
            FavoriID INT PRIMARY KEY IDENTITY(1,1),
            KullaniciID INT NOT NULL,
            KitapID INT NOT NULL,
            Tarih DATETIME DEFAULT GETDATE(),
            CONSTRAINT FK_Fav_User FOREIGN KEY (KullaniciID) REFERENCES Kullanicilar(KullaniciID),
            CONSTRAINT FK_Fav_Book FOREIGN KEY (KitapID) REFERENCES Kitaplar(KitapID),
            CONSTRAINT UQ_Fav UNIQUE (KullaniciID, KitapID) -- Aynı kitabı iki kere favorileyemesin
        )
        """
        cursor.execute(sql)
        conn.commit()
        print("✅ 'KitapFavoriler' tablosu hazır!")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_wishlist_table()