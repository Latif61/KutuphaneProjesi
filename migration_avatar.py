from src.utils.db import db

def add_avatar_column():
    print("⏳ Avatar sütunu ekleniyor...")
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        # Eğer sütun yoksa ekle
        sql = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Kullanicilar' AND COLUMN_NAME = 'Avatar')
        BEGIN
            ALTER TABLE Kullanicilar ADD Avatar NVARCHAR(50) DEFAULT 'avatar1';
        END
        """
        cursor.execute(sql)
        conn.commit()
        print("✅ 'Avatar' sütunu başarıyla eklendi!")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_avatar_column()