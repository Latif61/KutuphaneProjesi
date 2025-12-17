from src.utils.db import db

def update_book_cover():
    print("📚 --- KİTAP KAPAK GÜNCELLEME ARACI ---")
    
    # 1. Kullanıcıdan ISBN iste
    isbn = input("👉 Resmi değişecek kitabın ISBN numarasını girin: ").strip()
    
    if not isbn:
        print("❌ ISBN boş olamaz!")
        return

    # 2. Kitabın var olup olmadığını kontrol et
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT KitapAdi, ResimURL FROM Kitaplar WHERE ISBN = ?", (isbn,))
        row = cursor.fetchone()
        
        if not row:
            print("❌ Bu ISBN numarasına ait kitap bulunamadı!")
            return
        
        print(f"\n📖 Bulunan Kitap: {row[0]}")
        print(f"🖼️  Şu anki Resim: {row[1] if row[1] else 'YOK'}")
        
        # 3. Yeni Resim Linkini İste
        print("\n(Google Görseller'den beğendiğin kapağın linkini kopyala ve buraya yapıştır)")
        new_url = input("👉 Yeni Resim URL'si: ").strip()
        
        if not new_url:
            print("❌ İşlem iptal edildi (URL girmediniz).")
            return

        # 4. Güncelle
        cursor.execute("UPDATE Kitaplar SET ResimURL = ? WHERE ISBN = ?", (new_url, isbn))
        conn.commit()
        
        print(f"\n✅ BAŞARILI! '{row[0]}' kitabının kapağı güncellendi.")
        
    except Exception as e:
        print(f"❌ HATA: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_book_cover()