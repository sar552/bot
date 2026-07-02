#!/usr/bin/env bash
# Postgres bazasini backup qiladi. Har 6 soatda cron orqali ishlaydi.
# Faqat oxirgi KEEP ta backup saqlanadi, eskilari avtomatik o'chiriladi.
set -euo pipefail

# Loyiha papkasi (skript joyidan bir yuqori)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"

DB_CONTAINER="bot-db-1"
DB_USER="penbot"
DB_NAME="penbot"
KEEP=3   # nechta backup saqlansin

mkdir -p "$BACKUP_DIR"
TS="$(date +%F_%H-%M-%S)"
OUT="$BACKUP_DIR/penbot_${TS}.sql.gz"

# Backup olish (gzip bilan siqilgan)
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$OUT"

# Eng yangi KEEP tasini qoldirib, qolganini o'chirish
ls -1t "$BACKUP_DIR"/penbot_*.sql.gz 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f

echo "$(date '+%F %T') backup OK -> $OUT ($(du -h "$OUT" | cut -f1))"
