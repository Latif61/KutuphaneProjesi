from src.utils.db import db

def avatar_sutunu_ekle():
    print("⏳ Veritabanı güncelleniyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Avatar sütununu eklemeye çalışıyoruz
        # Varsayılan olarak 'avatar1' seçili gelsin diyoruz
        cursor.execute("ALTER TABLE Kullanicilar ADD Avatar NVARCHAR(50) DEFAULT 'avatar1'")
        conn.commit()
        print("✅ BAŞARILI! 'Avatar' sütunu eklendi.")
    except Exception as e:
        # Eğer sütun zaten varsa hata verir, onu yakalıyoruz
        if "Column names in each table must be unique" in str(e):
            print("ℹ️ Bilgi: 'Avatar' sütunu zaten varmış, sorun yok.")
        else:
            print(f"❌ Bir hata oluştu: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    avatar_sutunu_ekle()