#!/bin/bash
# Sunucuda git pull / güncelleme öncesi proje dizininin tam yedeğini tar.gz olarak alır.
# Kullanım: Sunucuda proje köküne (veya bir üst dizine) kopyalayıp çalıştırın.
#
#   scp deploy/backup_before_pull.sh user@sunucu:/opt/subu_chatbot_v2/
#   ssh user@sunucu "cd /opt/subu_chatbot_v2 && chmod +x backup_before_pull.sh && ./backup_before_pull.sh"
#
# Yedekler varsayılan olarak: /opt/backups/subu/ veya PROJECT_ROOT/../backups/

set -e

# Sunucudaki proje kök dizini (backend ve frontend burada veya içinde)
PROJECT_ROOT="${PROJECT_ROOT:-/opt/subu_chatbot_v2}"
# Alternatif: /opt/local_chatbot_subu

BACKUP_BASE="${BACKUP_BASE:-/opt/backups/subu}"
DATE=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="subu_project_full_${DATE}.tar.gz"
BACKUP_DIR="$BACKUP_BASE"
BACKUP_PATH="$BACKUP_DIR/$ARCHIVE_NAME"

if [ ! -d "$PROJECT_ROOT" ]; then
  echo "Hata: Proje dizini bulunamadi: $PROJECT_ROOT"
  echo "PROJECT_ROOT ortam degiskeni ile belirtebilirsiniz: PROJECT_ROOT=/opt/local_chatbot_subu $0"
  exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "Yedekleniyor: $PROJECT_ROOT -> $BACKUP_PATH"
# Proje dizinini tar.gz yap (venv mümkünse hariç tutulur - daha küçük yedek)
tar --exclude='venv' --exclude='__pycache__' --exclude='node_modules' \
  --exclude='.git' \
  -czf "$BACKUP_PATH" -C "$(dirname "$PROJECT_ROOT")" "$(basename "$PROJECT_ROOT")"

echo "Yedek tamamlandi: $BACKUP_PATH"
ls -lh "$BACKUP_PATH"

# Son 5 yedegi tut (istege bagli)
cd "$BACKUP_DIR"
ls -t subu_project_full_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
echo "Son yedekler:"
ls -lt subu_project_full_*.tar.gz 2>/dev/null || true
