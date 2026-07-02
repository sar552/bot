# Aqlli Ruchka Telegram Bot — System Architecture

> Stack: **Python 3.11+ / aiogram 3** · **PostgreSQL** (asosiy baza) + **Google Sheets** (admin uchun eksport/sync) · **Telegram ichida admin menyu**

Bu hujjat TZ asosida botning to'liq texnik arxitekturasini belgilaydi. Asosiy e'tibor: kod va bonus berishda **atomiklik** va **race condition'ni oldini olish**.

---

## 1. Arxitektura umumiy ko'rinishi (High-level)

```
                         ┌──────────────────────────┐
                         │      Telegram API         │
                         └────────────┬─────────────┘
                                      │ long polling / webhook
                         ┌────────────▼─────────────┐
                         │        BOT (aiogram 3)    │
                         │  ┌────────────────────┐   │
   Foydalanuvchi  ◄──────┤  │  Handlers / Routers│   │
                         │  │  + FSM (holatlar)  │   │
                         │  └─────────┬──────────┘   │
                         │  ┌─────────▼──────────┐   │
   Admin  ◄──────────────┤  │  Service layer     │   │
                         │  │ (biznes-logika)    │   │
                         │  └─────────┬──────────┘   │
                         │  ┌─────────▼──────────┐   │
                         │  │ Repository (DB)    │   │
                         │  └─────────┬──────────┘   │
                         └────────────┼─────────────┘
                                      │ asyncpg / SQLAlchemy
                         ┌────────────▼─────────────┐
                         │       PostgreSQL          │  ◄── haqiqat manbai (source of truth)
                         │  users / codes / bonuses  │      transaction + row lock
                         │  + audit_log, rate_limit  │
                         └────────────┬─────────────┘
                                      │ (bir tomonlama, fon vazifa)
                         ┌────────────▼─────────────┐
                         │     Google Sheets         │  ◄── admin uchun "oyna" (read-only ko'rinish)
                         │  Users / Codes / Bonuses  │      + Sheets'dan import (yangi kodlar)
                         └──────────────────────────┘
```

**Asosiy printsip:** Postgres — yagona haqiqat manbai. Sheets faqat (a) adminlar ko'rishi uchun eksport, (b) yangi ruchka/bonus kodlarini ommaviy import qilish uchun ishlatiladi. Bonus berish logikasi **hech qachon** Sheets'ga tayanmaydi — shu sabab race condition Postgres transaction orqali to'liq hal qilinadi.

---

## 2. Texnologiyalar (Tech stack)

| Qatlam | Texnologiya | Sabab |
|---|---|---|
| Til | Python 3.11+ | async, keng ekosistema |
| Bot framework | aiogram 3.x | zamonaviy async, FSM, router |
| DB | PostgreSQL 15+ | transaction, `FOR UPDATE SKIP LOCKED` atomiklik uchun |
| DB driver/ORM | SQLAlchemy 2.0 (async) + asyncpg | type-safe, migration mos |
| Migration | Alembic | sxema versiyalash |
| FSM storage | Redis (yoki Postgres) | holatni saqlash, restart'da yo'qolmaydi |
| Sheets | gspread / Google Sheets API v4 | eksport + import |
| Config | pydantic-settings + `.env` | token va sozlamalar |
| Logging | structlog / loguru | strukturali log, xatolarni kuzatish |
| Deploy | Docker + docker-compose | 24/7, izolyatsiya |
| Scheduler | APScheduler | bonus muddati (expired), reminder, Sheets sync |

---

## 3. Loyiha tuzilmasi (Project structure)

```
bot/
├── app/
│   ├── main.py                  # entrypoint: bot + dispatcher ishga tushirish
│   ├── config.py                # pydantic settings (.env)
│   │
│   ├── handlers/                # Telegram update'larini qabul qilish (controller)
│   │   ├── start.py             # /start, til (kelajakda), registratsiya kirishi
│   │   ├── registration.py      # ism + telefon olish (FSM)
│   │   ├── menu.py              # asosiy menyu
│   │   ├── product.py           # video + ma'lumot bo'limlari
│   │   ├── channels.py          # sotuv kanallari (linklar + click log)
│   │   ├── bonus.py             # kod kiritish → bonus berish flow
│   │   ├── faq.py               # savol-javob
│   │   ├── operator.py          # operatorga bog'lanish
│   │   └── admin/               # admin-only handlerlar
│   │       ├── __init__.py
│   │       ├── users.py         # foydalanuvchilar ro'yxati
│   │       ├── codes.py         # kodlarni ko'rish/qo'shish/block
│   │       ├── bonuses.py       # bonuslarni ko'rish/status o'zgartirish
│   │       └── broadcast.py     # ommaviy xabar
│   │
│   ├── services/                # biznes-logika (handlerlardan mustaqil)
│   │   ├── registration_service.py
│   │   ├── bonus_service.py     # ⭐ atomik kod-tekshirish + bonus berish
│   │   ├── rate_limit_service.py# noto'g'ri kod cheklovi (5 marta → 10 daqiqa)
│   │   ├── channel_service.py   # tracking/click log
│   │   └── sheets_service.py    # Postgres → Sheets eksport, Sheets → Postgres import
│   │
│   ├── db/
│   │   ├── models.py            # SQLAlchemy modellar
│   │   ├── repositories.py      # CRUD + atomik so'rovlar
│   │   ├── session.py           # async engine/session factory
│   │   └── enums.py             # CodeStatus, BonusStatus
│   │
│   ├── keyboards/               # inline + reply tugmalar
│   │   ├── menu.py
│   │   ├── bonus.py
│   │   └── admin.py
│   │
│   ├── states/                  # FSM holatlar
│   │   ├── registration.py
│   │   └── bonus.py
│   │
│   ├── middlewares/
│   │   ├── db.py                # har update'ga DB session berish
│   │   ├── user.py              # foydalanuvchini yuklash/yaratish
│   │   ├── admin.py             # admin ID tekshirish
│   │   └── throttling.py        # umumiy flood himoyasi
│   │
│   ├── texts/                   # barcha bot matnlari (kelajakda i18n)
│   │   └── uz.py
│   │
│   └── utils/
│       ├── validators.py        # telefon, kod formatini tekshirish
│       └── logging.py
│
├── migrations/                  # Alembic
├── tests/                       # TZ §17 test holatlari
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── ARCHITECTURE.md
```

**Qatlamlash (layering):** `handlers → services → repositories → db`. Handler faqat Telegram bilan gaplashadi; biznes-logika service'da; DB so'rovlari repository'da. Bu test va kengaytirishni osonlashtiradi.

---

## 4. Ma'lumotlar bazasi sxemasi (PostgreSQL)

### 4.1. `users`
```sql
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    telegram_id     BIGINT UNIQUE NOT NULL,
    username        TEXT,
    full_name       TEXT NOT NULL,
    phone           TEXT,
    language        TEXT DEFAULT 'uz',
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_telegram_id ON users (telegram_id);
```

### 4.2. `codes` (ruchka kodlari)
```sql
CREATE TYPE code_status AS ENUM ('unused', 'used', 'blocked');

CREATE TABLE codes (
    id                  BIGSERIAL PRIMARY KEY,
    code                TEXT UNIQUE NOT NULL,          -- normalizatsiya: UPPER + TRIM
    status              code_status NOT NULL DEFAULT 'unused',
    used_by_telegram_id BIGINT,
    used_by_name        TEXT,
    used_by_phone       TEXT,
    used_by_username    TEXT,
    used_at             TIMESTAMPTZ,
    note                TEXT,                          -- partiya raqami va h.k.
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX idx_codes_code ON codes (code);
CREATE INDEX idx_codes_status ON codes (status);
```

### 4.3. `bonuses` (10% bonuslar — oldindan yuklanadi)
```sql
CREATE TYPE bonus_status AS ENUM ('unused', 'assigned', 'used', 'expired', 'blocked');

CREATE TABLE bonuses (
    id                      BIGSERIAL PRIMARY KEY,
    bonus_code              TEXT UNIQUE NOT NULL,
    discount_percent        INT NOT NULL DEFAULT 10,
    status                  bonus_status NOT NULL DEFAULT 'unused',
    assigned_to_telegram_id BIGINT,
    assigned_to_name        TEXT,
    assigned_to_phone       TEXT,
    assigned_to_username    TEXT,
    source_code_id          BIGINT REFERENCES codes(id),  -- qaysi ruchka kodi orqali berilgan
    assigned_at             TIMESTAMPTZ,
    used_at                 TIMESTAMPTZ,
    expires_at              TIMESTAMPTZ,
    note                    TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_bonuses_status ON bonuses (status);
-- bitta bonus bitta userga: assigned bo'lganda telegram_id unique bo'lishi shart emas,
-- chunki bir user faqat bitta bonus oladi — buni service logikasi ta'minlaydi.
```

### 4.4. `rate_limits` (noto'g'ri kod cheklovi — TZ §8.11.13)
```sql
CREATE TABLE rate_limits (
    telegram_id     BIGINT PRIMARY KEY,
    failed_attempts INT NOT NULL DEFAULT 0,
    blocked_until   TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 4.5. `channel_clicks` (sotuv kanali tracking — TZ §7)
```sql
CREATE TABLE channel_clicks (
    id           BIGSERIAL PRIMARY KEY,
    telegram_id  BIGINT NOT NULL,
    channel      TEXT NOT NULL,          -- 'telegram' | 'instagram' | 'uzum' ...
    clicked_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 4.6. `audit_log` (admin amallari + muhim hodisalar)
```sql
CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    actor_id    BIGINT,                  -- admin yoki tizim
    action      TEXT NOT NULL,           -- 'code_blocked', 'bonus_assigned', ...
    entity      TEXT,
    entity_id   BIGINT,
    details     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 5. ⭐ Eng muhim oqim: Atomik kod tekshirish va bonus berish

Bu TZ'ning eng kritik qismi (§8, §15, §19). Ikki foydalanuvchi bir vaqtda bir kodni yoki bir bonusni olmasligi **kafolatlanishi** kerak. Postgres bilan buni `SERIALIZABLE`-ga muqobil, soddaroq va tezroq usul — bitta **transaction ichida row-level lock** orqali hal qilamiz.

### 5.1. Algoritm (`bonus_service.claim_bonus`)

```python
async def claim_bonus(session, user, raw_code: str) -> ClaimResult:
    code_str = raw_code.strip().upper()          # normalizatsiya (TZ §8.2)

    async with session.begin():                  # bitta atomik transaction
        # 1) Ruchka kodini LOCK bilan o'qiymiz — boshqa transaction kutadi
        code = await session.scalar(
            select(Code)
            .where(Code.code == code_str)
            .with_for_update()                    # FOR UPDATE — qatorni qulflaydi
        )

        # 2) Holatlarni tekshirish
        if code is None:
            return ClaimResult.NOT_FOUND          # TZ §8.6
        if code.status == CodeStatus.blocked:
            return ClaimResult.BLOCKED            # TZ §8.8
        if code.status == CodeStatus.used:
            return ClaimResult.ALREADY_USED       # TZ §8.7

        # 3) Bo'sh bonusni LOCK + SKIP LOCKED bilan olamiz
        #    SKIP LOCKED → parallel so'rovlar bir xil bonusni olmaydi
        bonus = await session.scalar(
            select(Bonus)
            .where(Bonus.status == BonusStatus.unused)
            .order_by(Bonus.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        # 4) Ruchka kodini band qilamiz (bonus bo'lmasa ham — xarid tasdiqlandi)
        code.status              = CodeStatus.used
        code.used_by_telegram_id = user.telegram_id
        code.used_by_name        = user.full_name
        code.used_by_phone       = user.phone
        code.used_by_username    = user.username
        code.used_at             = now()

        if bonus is None:
            # TZ §8.5 — kod to'g'ri, lekin bonus qolmagan → operatorga
            await audit(session, 'code_used_no_bonus', code.id, user)
            return ClaimResult.CONFIRMED_NO_BONUS

        # 5) Bonusni shu userga biriktiramiz
        bonus.status                  = BonusStatus.assigned
        bonus.assigned_to_telegram_id = user.telegram_id
        bonus.assigned_to_name        = user.full_name
        bonus.assigned_to_phone       = user.phone
        bonus.assigned_to_username    = user.username
        bonus.source_code_id          = code.id
        bonus.assigned_at             = now()
        bonus.expires_at              = now() + timedelta(days=30)  # TZ §8.10 (ixtiyoriy)

        await audit(session, 'bonus_assigned', bonus.id, user)
        # transaction commit → ikkala o'zgarish birga saqlanadi yoki birga bekor bo'ladi
        return ClaimResult.SUCCESS(bonus.bonus_code, bonus.discount_percent)
```

**Nega bu xavfsiz:**
- `FOR UPDATE` ruchka kodi qatorini qulflaydi → bir kodni ikki user bir vaqtda ishlata olmaydi (TZ §17.20).
- `FOR UPDATE SKIP LOCKED` bonusda → parallel ikki tranzaksiya **har xil** bo'sh bonus oladi, hech qachon bitta bonusni ikkovi olmaydi (TZ §17.21, §15).
- Hammasi bitta transaction → yo to'liq bajariladi, yo to'liq bekor (atomiklik, TZ §14.14).
- Sheets umuman ishtirok etmaydi → tarmoq/Sheets sekinligi atomiklikka ta'sir qilmaydi.

### 5.2. Natijaga qarab javoblar (handler)

| Natija | Bot javobi (TZ) | Tugmalar |
|---|---|---|
| `SUCCESS` | §8.4 — "Tabriklaymiz! ... bonus kodingiz: …" | Bonusdan foydalanish / Sotuv kanallari / Operator / Menyu |
| `CONFIRMED_NO_BONUS` | §8.5 — "Xaridingiz tasdiqlandi … operator bilan bog'laning" | Operator / Sotuv kanallari / Menyu |
| `NOT_FOUND` | §8.6 — "Kiritilgan kod topilmadi …" | Qayta kiritish / Operator / Menyu |
| `ALREADY_USED` | §8.7 — "Bu kod avval aktivlashtirilgan …" | Operator / Menyu |
| `BLOCKED` | §8.8 — "Bu kod orqali bonus olish imkoniyati yo'q …" | Operator / Menyu |

`NOT_FOUND` holatida `rate_limit_service` chaqiriladi: 5 marta xato → `blocked_until = now() + 10 min` (TZ §8.11.13).

---

## 6. Foydalanuvchi oqimi (FSM holatlar)

```
/start
  │
  ▼
[RegistrationState.waiting_name] ──► ism validatsiya (bo'sh emas, ≥2 belgi) ──► qayta so'rov agar xato
  │  (valid)
  ▼
[RegistrationState.waiting_phone] ──► "Kontakt yuborish" tugmasi yoki qo'lda
  │  +998 format validatsiya
  ▼  (users jadvaliga saqlanadi)
ASOSIY MENYU ◄──────────────────────────────┐
  ├─ 🎬 Video                                │
  ├─ 📖 Ma'lumot                             │  har bir bo'limdan
  ├─ 🛒 Sotib olish / kanallar              │  "Asosiy menyu" tugmasi
  ├─ 🎁 10% bonus olish                      │  qaytaradi
  │     └─[BonusState.waiting_code] ──► claim_bonus()
  ├─ ❓ Savol-javob                          │
  └─ ☎️ Operator                            │
─────────────────────────────────────────────┘
```

FSM storage **Redis**'da (yoki Postgres) — bot restart bo'lganda foydalanuvchi holati yo'qolmaydi (TZ §17.27).

Ro'yxatdan o'tgan foydalanuvchi `/start` bossa — to'g'ridan-to'g'ri asosiy menyuga o'tadi (qayta ism so'ralmaydi).

---

## 7. Admin moduli (Telegram ichida)

- Kirish: `config.ADMIN_IDS` ro'yxati orqali `admin.py` middleware tekshiradi. Boshqalarga admin handlerlar ko'rinmaydi (TZ §14.8).
- Funksiyalar (TZ §10):

| Buyruq / tugma | Vazifa |
|---|---|
| 👥 Foydalanuvchilar | ro'yxat + telefon (pagination) |
| 🔑 Kodlar | barcha / unused / used / blocked filtri |
| ➕ Kod qo'shish | bitta yoki fayl orqali ommaviy |
| 🚫 Kodni block | `status = blocked` |
| 🎁 Bonuslar | ro'yxat + status filtri |
| ➕ Bonus qo'shish | ommaviy yuklash |
| ✏️ Bonus status | qo'lda `assigned → used` va h.k. |
| 📣 Ommaviy xabar | barcha userlarga broadcast (throttling bilan) |
| 📊 Statistika | ro'yxatdan o'tganlar, ishlatilgan kodlar soni |

Har bir admin amali `audit_log`'ga yoziladi.

---

## 8. Google Sheets integratsiyasi (eksport + import)

Postgres asosiy bo'lgani uchun Sheets ikki yo'nalishda, lekin **cheklangan**:

1. **Eksport (Postgres → Sheets), bir tomonlama, fon:** APScheduler har N daqiqada `users`, `codes`, `bonuses` jadvallarini mos sheet'larga yozadi. Admin Sheets'da real holatni ko'radi (TZ §10 "Google Sheets orqali boshqarish" ko'rinishi).
2. **Import (Sheets → Postgres), faqat yangi kod/bonus:** Admin Sheets'ga yangi ruchka kod yoki bonus qatorlarini qo'shsa, `sheets_service.import_new()` ularni Postgres'ga `unused` holatda qo'shadi (dublikatlarni `UNIQUE` himoya qiladi).

> Muhim: bonus **berish** logikasi Sheets'ga **hech qachon** yozmaydi. Sheets sekin/uzilsa ham xaridor bonusi to'g'ri beriladi. Sheets — faqat "oyna".

---

## 9. Qo'shimcha tizim xizmatlari

- **Reminder (TZ §11.3):** APScheduler — botga kirib, kanalga o'tmagan/bonus olmagan userlarga 24 soatdan keyin eslatma. Telegram qoidalariga rioya (faqat botga yozganlar).
- **Bonus expiry (TZ §8.10):** kunlik job — `expires_at < now()` va `assigned` bonuslarni `expired` qiladi.
- **Operatorga bog'lash (TZ §11.4):** operator username linki yoki user xabarini admin chatga forward.
- **Sotuv kanallari linklari:** `config`/DB'da saqlanadi → admin o'zgartira oladi (TZ §7), bosilganda `channel_clicks`'ga log.

---

## 10. Konfiguratsiya (`.env`)

```env
BOT_TOKEN=...
ADMIN_IDS=11111111,22222222
OPERATOR_USERNAME=@operator

DATABASE_URL=postgresql+asyncpg://bot:pass@db:5432/penbot
REDIS_URL=redis://redis:6379/0

GOOGLE_SHEETS_CREDENTIALS=/secrets/service_account.json
GOOGLE_SPREADSHEET_ID=...
SHEETS_SYNC_INTERVAL_MIN=10

PRODUCT_VIDEO_FILE_ID=...        # Telegram'ga bir marta yuklab file_id olinadi
CHANNEL_TELEGRAM_URL=https://t.me/...
CHANNEL_INSTAGRAM_URL=https://instagram.com/...
CHANNEL_UZUM_URL=https://uzum.uz/...

RATE_LIMIT_MAX_FAILS=5
RATE_LIMIT_BLOCK_MINUTES=10
BONUS_EXPIRY_DAYS=30
```

Maxfiy ma'lumotlar (token, service account) repository'ga kirmaydi — `.env` va Docker secrets orqali (TZ §14.5).

---

## 11. Deploy va ishonchlilik (24/7)

```yaml
# docker-compose.yml (qisqacha)
services:
  bot:
    build: .
    env_file: .env
    depends_on: [db, redis]
    restart: always          # crash bo'lsa avtomatik qayta ishga tushadi
  db:
    image: postgres:15
    volumes: [pgdata:/var/lib/postgresql/data]   # restart'da ma'lumot saqlanadi
    restart: always
  redis:
    image: redis:7
    restart: always
volumes: { pgdata: {} }
```

- **24/7 (TZ §14.9):** `restart: always` + VPS/cloud. Polling MVP uchun yetarli; yuk oshsa webhook.
- **Migration:** start'da `alembic upgrade head`.
- **Logging (TZ §14.10):** structlog → stdout → Docker log / fayl. Xatolar `audit_log` va log faylga.
- **Backup:** Postgres `pg_dump` kunlik (cron).

---

## 12. Test holatlari (TZ §17 → avtomatlashtirilgan)

`tests/` da `pytest` + `pytest-asyncio`, alohida test DB. Kritik testlar:

- ✅ To'liq registratsiya oqimi (ism + telefon validatsiya).
- ✅ To'g'ri kod → bonus beriladi, code=`used`, bonus=`assigned`.
- ✅ Noto'g'ri / used / blocked kod javoblari.
- ✅ Bonus qolmagan → `CONFIRMED_NO_BONUS`.
- ⭐ **Concurrency testi:** bitta kodga 2 parallel `claim_bonus` → faqat bittasi `SUCCESS`, ikkinchisi `ALREADY_USED`.
- ⭐ **Bonus concurrency:** 2 user 2 har xil kod bilan bir vaqtda → har biriga **har xil** bonus.
- ✅ Rate limit: 5 xato → 10 daqiqa blok.
- ✅ Restart'dan keyin ma'lumot saqlanadi.

---

## 13. Bosqichli reja (TZ §18 minimal versiya bilan moslangan)

**1-bosqich (MVP):** loyiha skeleti, DB sxema + migration, `/start` → registratsiya → menyu, video + ma'lumot, sotuv kanallari, **atomik kod→bonus oqimi**, operator. → TZ §18 ning 1–13 punktlari.

**2-bosqich:** Telegram admin menyu (ko'rish, kod/bonus qo'shish, status), rate-limit, audit log, Sheets eksport.

**3-bosqich:** Sheets import, broadcast, FAQ, reminder + bonus expiry scheduler.

**4-bosqich (keyingi):** ko'p tillilik (uz/ru/en), buyurtma formasi, referral, web admin panel — TZ §20.

---

## 14. Xavfsizlik nuqtalari (TZ §14, §19)

- Admin funksiyalar faqat `ADMIN_IDS` orqali.
- Telefon, kod, bonus — Postgres'da, repo'da emas; access cheklangan.
- Bir kod — bir marta (`FOR UPDATE`), bir bonus — bir userga (`SKIP LOCKED`).
- Barcha status o'zgarishlari transaction ichida (atomik).
- Flood/spam himoya: throttling middleware + kod rate-limit.
- Shaxsiy ma'lumotlar faqat ichki maqsadda (TZ §19).
