from src.utils.db import db

def debug_pending_requests():
    print("🔬 DETAYLI İNCELEME BAŞLIYOR...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # SQL Sorgusunu birebir deniyoruz
        sql = """
        SELECT i.IstekID, k.KitapAdi, u.Ad, u.Soyad, i.TalepTarihi, k.ResimURL
        FROM KitapIstekleri i
        JOIN Kitaplar k ON i.KitapID = k.KitapID
        JOIN Kullanicilar u ON i.KullaniciID = u.KullaniciID
        WHERE i.Durum = 'Bekliyor'
        ORDER BY i.TalepTarihi DESC
        """
        print("➡️ SQL Sorgusu çalıştırılıyor...")
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        print(f"📊 Bulunan Satır Sayısı: {len(rows)}")
        
        if len(rows) > 0:
            print("✅ Veri başarıyla çekildi! İşte ilk satır:")
            print(rows[0])
            
            # Python tarafındaki dönüştürme işlemini simüle edelim (Hata burada mı?)
            print("🔄 JSON formatına çevriliyor...")
            formatted_data = []
            for r in rows:
                formatted_data.append({
                    "id": r.IstekID, 
                    "kitap": r.KitapAdi, 
                    "ogrenci": f"{r.Ad} {r.Soyad}", 
                    "tarih": r.TalepTarihi.strftime('%d.%m.%Y'), 
                    "resim": r.ResimURL
                })
            print("✅ Dönüştürme Başarılı!")
            print(formatted_data)
        else:
            print("⚠️ Sorgu çalıştı ama sonuç boş döndü.")

    except Exception as e:
        print("\n🚨🚨🚨 HATA YAKALANDI! 🚨🚨🚨")
        print(f"Hata Mesajı: {e}")
        print("Muhtemelen sütun isimlerinde bir uyumsuzluk var.")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    debug_pending_requests()