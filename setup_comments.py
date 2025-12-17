from src.utils.db import db

def create_comment_table():
    print("⏳ Yorum tablosu kontrol ediliyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='KitapYorumlari' AND xtype='U')
        CREATE TABLE KitapYorumlari (
            YorumID INT PRIMARY KEY IDENTITY(1,1),
            KitapID INT NOT NULL,
            KullaniciID INT NOT NULL,
            YorumMetni NVARCHAR(MAX),
            YorumTarihi DATETIME DEFAULT GETDATE(),
            FOREIGN KEY (KitapID) REFERENCES Kitaplar(KitapID),
            FOREIGN KEY (KullaniciID) REFERENCES Kullanicilar(KullaniciID)
        )
        """
        cursor.execute(sql)
        conn.commit()
        print("✅ BAŞARILI: 'KitapYorumlari' tablosu hazır.")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        cursor.close(); conn.close()

if __name__ == "__main__":
    create_comment_table()