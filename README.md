# Aqlli Ruchka — Telegram Bot

Bolalar uchun aqlli ruchka va interaktiv kitoblar mahsulotini sotuvchi Telegram bot.
Foydalanuvchilarni ro'yxatga oladi, mahsulot haqida ma'lumot beradi, sotuv kanallariga
yo'naltiradi va ruchka kodi orqali xaridni tasdiqlab **bir martalik 10% bonus** beradi.

> Stack: **Python 3.11+ / aiogram 3** · **PostgreSQL** + **Google Sheets (eksport)** · **Redis (FSM)**
> To'liq texnik dizayn: [ARCHITECTURE.md](ARCHITECTURE.md)

## Asosiy xususiyatlar

- `/start` → ism + telefon olish (validatsiya bilan) → asosiy menyu
- Mahsulot videosi va batafsil ma'lumot
- Sotuv kanallari (Telegram, Instagram, Uzum) + click tracking
- **Atomik kod → bonus oqimi**: race condition'siz, Postgres `FOR UPDATE` / `SKIP LOCKED`
- Noto'g'ri kod uchun rate-limit (5 marta → 10 daqiqa blok)
- Savol-javob va operatorga bog'lanish
- Telegram ichida **admin panel**: foydalanuvchi/kod/bonus ko'rish, qo'shish, bloklash, status, ommaviy xabar
- Bonus muddati va Google Sheets eksporti — fon scheduler orqali

## Loyiha tuzilmasi

```
app/
├── main.py            # entrypoint
├── config.py          # .env sozlamalari
├── handlers/          # Telegram update'lari (start, registration, menu, product, channels, bonus, faq, operator, admin/)
├── services/          # biznes-logika (bonus_service ⭐, rate_limit, sheets, broadcast)
├── db/                # models, repositories, session, enums
├── keyboards/         # inline + reply tugmalar
├── middlewares/       # db session, user load, admin filter, throttling
├── states/            # FSM holatlar
├── texts/uz.py        # barcha matnlar
└── utils/             # validators, logging
migrations/            # Alembic
tests/                 # pytest (concurrency testlari)
```

## Ishga tushirish (Docker — tavsiya)

```bash
cp .env.example .env
# .env ni to'ldiring: BOT_TOKEN, ADMIN_IDS, OPERATOR_USERNAME, kanallar...

docker compose up -d --build
docker compose logs -f bot
```

Migration konteyner ishga tushganda avtomatik qo'llanadi (`alembic upgrade head`).

## Lokal ishga tushirish (Docker'siz)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Postgres va Redis kerak (masalan docker orqali faqat ularni ko'tarish):
docker compose up -d db redis

cp .env.example .env   # DATABASE_URL va REDIS_URL ni localhost'ga moslang
alembic upgrade head
python -m app.main
```

## Boshlang'ich ma'lumotlarni yuklash

Ruchka kodlari va bonuslar admin tomonidan kiritiladi:

1. Telegram'da botga `/admin` deb yozing (ID `ADMIN_IDS` da bo'lishi shart).
2. **➕ Kod qo'shish** — har qatorda bitta kod (`KOD | izoh` ham mumkin).
3. **➕ Bonus qo'shish** — har qatorda bitta bonus kodi (`BONUS10-XXXX | 10`).

> Videoni botga bir marta yuborib, `getUpdates`/log orqali `file_id` ni oling va
> `.env` dagi `PRODUCT_VIDEO_FILE_ID` ga qo'ying.

## Testlar

Concurrency testlari haqiqiy Postgres talab qiladi:

```bash
docker compose up -d db
export TEST_DATABASE_URL=postgresql+asyncpg://penbot:penbot@localhost:5432/penbot_test
createdb -h localhost -U penbot penbot_test   # yoki psql orqali
pip install -r requirements-dev.txt
pytest -v
```

`tests/test_bonus_service.py` quyidagilarni tekshiradi (TZ §17):
- to'g'ri/noto'g'ri/used/blocked kod holatlari
- bonus qolmagan holat (§8.5)
- ⭐ bitta kodni 2 user bir vaqtda → faqat bittasiga bonus
- ⭐ bitta bonus 2 userga berilib ketmasligi

## Xavfsizlik (TZ §14, §19)

- Admin funksiyalar faqat `ADMIN_IDS` orqali.
- Bir ruchka kodi — bir marta; bir bonus — bir foydalanuvchiga (DB lock bilan kafolat).
- Maxfiy ma'lumotlar `.env` / Docker secrets'da, repozitoriyga kirmaydi.
- Xatolar `logs/bot.log` ga yoziladi.
# bot
