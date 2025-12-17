from src.utils.db import db

def check_my_books():
    print("📚 Veritabanı kontrol ediliyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Toplam kaç kitap var?
        cursor.execute("SELECT COUNT(*) FROM Kitaplar")
        count = cursor.fetchone()[0]
        
        print(f"\n✅ MÜJDE! İçeride sapasağlam duran {count} adet kitap var.")
        print("-" * 40)
        
        # 2. İlk 10 kitabın ismini yazdıralım
        cursor.execute("SELECT TOP 10 KitapAdi, ISBN FROM Kitaplar")
        rows = cursor.fetchall()
        
        if rows:
            print("İşte bazılarının isimleri:")
            for row in rows:
                print(f"📖 {row.KitapAdi} (ISBN: {row.ISBN})")
        else:
            print("Kitap tablosu boş görünüyor (Bu garip).")
            
        print("-" * 40)
        print("Gördüğün gibi verilerin silinmemiş, sadece ekrana gelmiyor.")

    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_my_books()