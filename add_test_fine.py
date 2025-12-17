from src.utils.db import db
import datetime

def add_fake_fine():
    print("😈 Kötü Polis İş Başında: Ceza Kesiliyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Eski kayıtlardaki NULL değerleri düzelt (Önemli!)
        cursor.execute("UPDATE Cezalar SET OdendiMi = 0 WHERE OdendiMi IS NULL")
        
        # 2. Bir kullanıcı ve ödünç işlemi bul
        cursor.execute("SELECT TOP 1 OduncID, KullaniciID FROM OduncIslemleri")
        row = cursor.fetchone()
        
        if row:
            odunc_id = row[0]
            # 3. 50 TL Ceza Çak
            cursor.execute("INSERT INTO Cezalar (OduncID, Tutar, OdendiMi) VALUES (?, 50.00, 0)", (odunc_id,))
            conn.commit()
            print(f"✅ BAŞARILI: {odunc_id} nolu işleme 50 TL ceza eklendi.")
            print("👉 Şimdi sayfayı yenile, sol tarafta borcu seç, kart alanı açılacak!")
        else:
            print("❌ HATA: Hiç ödünç işlemi yok, ceza kesemedim. Önce bir kitap al!")

    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        cursor.close(); conn.close()

if __name__ == "__main__":
    add_fake_fine()