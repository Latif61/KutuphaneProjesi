from src.utils.db import db

def create_request_table():
    print("⏳ Talep tablosu oluşturuluyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        # Tablo yoksa oluştur
        sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='KitapIstekleri' AND xtype='U')
        CREATE TABLE KitapIstekleri (
            IstekID INT PRIMARY KEY IDENTITY(1,1),
            KullaniciID INT NOT NULL,
            KitapID INT NOT NULL,
            TalepTarihi DATETIME DEFAULT GETDATE(),
            Durum NVARCHAR(20) DEFAULT 'Bekliyor', -- Bekliyor, Onaylandi, Reddedildi
            FOREIGN KEY (KullaniciID) REFERENCES Kullanicilar(KullaniciID),
            FOREIGN KEY (KitapID) REFERENCES Kitaplar(KitapID)
        )
        """
        cursor.execute(sql)
        conn.commit()
        print("✅ BAŞARILI: 'KitapIstekleri' tablosu hazır.")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        cursor.close(); conn.close()

if __name__ == "__main__":
    create_request_table()