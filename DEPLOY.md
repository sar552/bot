# 🚀 Serverga qo'yish qo'llanmasi

## 1-qism. O'zgartiriladigan matn va sozlamalar

### A) Bot matnlari — `app/texts/uz.py`
Barcha bot xabarlari shu bitta faylda. Quyidagilarni o'zingizga moslang:

| O'zgaruvchi | Nima matni |
|---|---|
| `START` | /start dagi salomlashuv |
| `ASK_PHONE` | Telefon so'rash matni |
| `VIDEO_CAPTION` | Video ostidagi matn |
| `PRODUCT_INFO` | 📖 Mahsulot haqida ma'lumot (to'liq matn) |
| `CHANNELS` | Sotuv kanallari matni |
| `ASK_CODE` | Bonus kodini so'rash |
| `bonus_success(...)` | Bonus berilgandagi tabrik matni |
| `BOOKS_INTRO` | Kitoblar bo'limi matni |
| `book_ask_code(...)` | Kitob uchun kod so'rash |
| `FAQ` | ❓ Savol-javoblar (savollar + javoblar) |
| Boshqa xabarlar | Xato/blok/operator matnlari |

> Matnni o'zgartirgach: `docker compose up -d --build`

### B) Linklar va tokenlar — `.env`
Bularni **albatta** o'zingiznikiga almashtiring (hozir ba'zilari namunaviy):

```env
BOT_TOKEN=...                       # @BotFather dan
ADMIN_IDS=5638486976               # admin Telegram ID(lar), vergul bilan
OPERATOR_USERNAME=@sizning_operator

PRODUCT_VIDEO_FILE_ID=...          # botga video yuborib olingan file_id

# ⚠️ Hozir namunaviy — HAQIQIY havolalarni qo'ying:
CHANNEL_TELEGRAM_URL=https://t.me/sizning_kanal
CHANNEL_INSTAGRAM_URL=https://instagram.com/sizning_sahifa
CHANNEL_UZUM_URL=https://uzum.uz/sizning_dokon
CHANNEL_OTHER_URL=

# Xavfsizlik (biznes qoidalari)
RATE_LIMIT_MAX_FAILS=5
RATE_LIMIT_BLOCK_MINUTES=10
BONUS_EXPIRY_DAYS=30
BOOK_CODE_MAX_FAILS=10

# Google Sheets (ishlatsangiz)
GOOGLE_SHEETS_CREDENTIALS=/secrets/service_account.json
GOOGLE_SPREADSHEET_ID=...
```

### C) ⚠️ Production uchun DB parolini o'zgartiring
`docker-compose.yml` va `.env`'dagi `penbot:penbot` — bu **standart parol**. Serverda kuchliroq parolga almashtiring:
- `docker-compose.yml` → `POSTGRES_PASSWORD`
- `.env` → `DATABASE_URL` dagi parol

---

## 2-qism. Server uchun hardware

Bot yengil (aiogram + Postgres + Redis). Talablar kichik:

| Daraja | CPU | RAM | Disk | Kimga |
|---|---|---|---|---|
| **Minimal** | 1 vCPU | 1 GB | 20 GB SSD | Minglab foydalanuvchigacha yetadi |
| **Tavsiya** | 2 vCPU | 2 GB | 25–40 GB SSD | Bemalol, zaxira bilan |

- **OS:** Ubuntu 22.04 yoki 24.04 LTS
- **Kerakli:** Docker + Docker Compose
- **Tarmoq:** oddiy internet (statik IP shart emas, polling ishlatadi)
- **Disk:** kitob `.tnb` fayllari hajmiga qarab oshiring (masalan 500 ta kitob × 5 MB = ~2.5 GB)

> Bu bot uchun **eng arzon VPS** (1 GB RAM, ~5$/oy) ham yetarli. O'sish bo'lsa 2 GB oling.

---

## 3-qism. Serverga o'rnatish qadamlari

```bash
# 1. Serverga kiring (SSH)
ssh root@SERVER_IP

# 2. Docker o'rnatish (Ubuntu)
curl -fsSL https://get.docker.com | sh

# 3. Loyihani serverga ko'chiring (git yoki scp)
git clone <repo>   # yoki: scp -r bot/ root@SERVER_IP:~/bot

cd bot

# 4. .env ni to'ldiring (yuqoridagi B qism)
cp .env.example .env
nano .env

# 5. (Sheets ishlatsangiz) JSON kalitni qo'ying
mkdir -p secrets
# service_account.json ni secrets/ ga ko'chiring

# 6. Ishga tushiring
docker compose up -d --build

# 7. Loglarni tekshiring
docker compose logs -f bot
```

### Foydali buyruqlar (serverda)
```bash
docker compose ps            # holat
docker compose logs -f bot   # jonli log
docker compose restart bot   # qayta ishga tushirish
docker compose down          # to'xtatish (ma'lumot saqlanadi)
docker compose up -d --build # yangilashdan keyin
```

### Avtomatik zaxira (backup) — har 6 soatda, oxirgi 3 tasi saqlanadi

Loyihada `scripts/backup.sh` bor: DB'ni `backups/` papkasiga oladi va faqat
oxirgi **3 ta** backupni saqlab, eskilarini o'chiradi.

**Serverda bir marta cron'ga qo'yish:**
```bash
chmod +x ~/bot/scripts/backup.sh
crontab -e
```
Ochilgan faylga quyidagi qatorni qo'shing (har 6 soatda: 00:00, 06:00, 12:00, 18:00):
```
0 */6 * * * /root/bot/scripts/backup.sh >> /root/bot/backups/backup.log 2>&1
```
> Yo'l `/root/bot/...` — agar boshqa foydalanuvchida bo'lsangiz, `~/bot` o'rniga to'g'ri yo'lni yozing (`pwd` bilan tekshiring).

**Qo'lda tekshirish:**
```bash
~/bot/scripts/backup.sh        # darhol backup oladi
ls -lh ~/bot/backups/          # backuplarni ko'rish
```

**Backupdan tiklash (kerak bo'lsa):**
```bash
gunzip -c ~/bot/backups/penbot_YYYY-MM-DD_HH-MM-SS.sql.gz | \
  docker exec -i bot-db-1 psql -U penbot -d penbot
```

> Kitob fayllari (`books/`) alohida — vaqti-vaqti bilan nusxalang:
> `tar czf ~/books_$(date +%F).tar.gz ~/bot/books/`

---

## Xulosa
- **Matnlar:** `app/texts/uz.py`
- **Linklar/token:** `.env`
- **Server:** 1–2 GB RAM li Ubuntu VPS + Docker
- **Ishga tushirish:** `docker compose up -d --build`
