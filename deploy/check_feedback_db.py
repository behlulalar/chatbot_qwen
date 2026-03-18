#!/usr/bin/env python3
"""
Sunucuda geri bildirim (response_feedbacks) tablosunun var olup olmadığını
ve kayıt sayısını kontrol eder. Backend klasöründen çalıştırılmalı:
  cd ~/behlul/backend && source venv/bin/activate && python ../deploy/check_feedback_db.py
  # veya proje kökünden:
  cd /path/to/documentation_chatbot_final_subu/backend && source venv/bin/activate && python ../deploy/check_feedback_db.py
"""
import os
import sys

# Backend'in app'ini yükleyebilmek için path ekle (script deploy/ içinde)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, "backend")
if not os.path.isdir(backend_path):
    backend_path = project_root  # sunucuda ~/behlul/backend içinden çalıştırılıyorsa
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
os.chdir(backend_path)

def main():
    try:
        from app.database import engine
        from sqlalchemy import text
    except Exception as e:
        print(f"Hata (import): {e}")
        print("Çalıştırma: cd backend && source venv/bin/activate && python ../deploy/check_feedback_db.py")
        sys.exit(1)

    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT COUNT(*) FROM response_feedbacks"))
            count = r.scalar()
            print(f"response_feedbacks tablosu mevcut.")
            print(f"Toplam geri bildirim sayısı: {count}")
    except Exception as e:
        print(f"Hata: {e}")
        print("Tablo yok veya veritabanına bağlanılamıyor. .env içinde DATABASE_URL doğru mu?")
        sys.exit(1)

if __name__ == "__main__":
    main()
