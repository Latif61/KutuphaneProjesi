from src.utils.db import db

def update_fines_table():
    print("⏳ Cezalar tablosu güncelleniyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        # ÖdendiMi sütunu yoksa ekle
        try:
            cursor.execute("SELECT TOP 1 OdendiMi FROM Cezalar")
        except:
            print("➕ 'OdendiMi' sütunu ekleniyor...")
            cursor.execute("ALTER TABLE Cezalar ADD OdendiMi BIT DEFAULT 0")

        # OdemeTarihi sütunu yoksa ekle
        try:
            cursor.execute("SELECT TOP 1 OdemeTarihi FROM Cezalar")
        except:
            print("➕ 'OdemeTarihi' sütunu ekleniyor...")
            cursor.execute("ALTER TABLE Cezalar ADD OdemeTarihi DATETIME NULL")
            
        conn.commit()
        print("✅ BAŞARILI: Tablo ödeme almaya hazır!")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        cursor.close(); conn.close()

if __name__ == "__main__":
    update_fines_table()