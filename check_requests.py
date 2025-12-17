from src.utils.db import db

def check_db():
    print("🕵️‍♂️ VERİTABANI AJANI ÇALIŞIYOR...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Tablo var mı?
        try:
            cursor.execute("SELECT Count(*) FROM KitapIstekleri")
            count = cursor.fetchone()[0]
            print(f"✅ Tablo bulundu. Toplam Kayıt Sayısı: {count}")
        except:
            print("❌ KRİTİK HATA: 'KitapIstekleri' tablosu YOK! Migration çalıştırılmamış.")
            return

        # 2. Bekleyen Talep Var mı?
        print("\n--- BEKLEYEN TALEPLER LİSTESİ ---")
        sql = """
        SELECT i.IstekID, k.KitapAdi, u.Ad, i.Durum 
        FROM KitapIstekleri i
        JOIN Kitaplar k ON i.KitapID = k.KitapID
        JOIN Kullanicilar u ON i.KullaniciID = u.KullaniciID
        WHERE i.Durum = 'Bekliyor'
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        if len(rows) == 0:
            print("⚠️ HİÇ BEKLEYEN TALEP YOK. (Sorun Öğrenci Sayfasında)")
        else:
            for row in rows:
                print(f"📌 ID: {row.IstekID} | Kitap: {row.KitapAdi} | Öğrenci: {row.Ad} | Durum: {row.Durum}")
            print("\n✅ SONUÇ: Veritabanında talep VAR. (Sorun Admin Sayfasında)")

    except Exception as e:
        print(f"❌ HATA: {e}")
    finally:
        cursor.close(); conn.close()

if __name__ == "__main__":
    check_db()