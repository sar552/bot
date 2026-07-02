# 🟢 Google Sheets jonli ulashni yoqish — qadam-baqadam

Bu qo'llanma DB'ni Google Sheets'da **jonli ko'rish** va Sheets'da **kod/bonus kiritib turish** uchun.

> Yo'nalish: DB ⇄ Sheets. Bot har `SHEETS_SYNC_INTERVAL_MIN` daqiqada:
> 1. Sheets'dagi **Codes** va **Bonuses** varaqlaridan yangi kodlarni o'qib, DB'ga qo'shadi;
> 2. DB'ning to'liq holatini Sheets'ga qaytaradi (UI doim yangilanadi).

---

## 1. Google Cloud loyiha yaratish

1. [console.cloud.google.com](https://console.cloud.google.com) ga kiring.
2. Yuqoridagi loyiha ro'yxatidan **New Project** → nom bering (masalan `penbot`) → **Create**.

## 2. Sheets API'ni yoqish

1. Chap menyu → **APIs & Services → Library**.
2. **Google Sheets API** ni qidiring → **Enable**.
3. Xuddi shunday **Google Drive API** ni ham **Enable** qiling.

## 3. Service Account + JSON kalit

1. **APIs & Services → Credentials** → **Create Credentials → Service account**.
2. Nom bering (masalan `penbot-bot`) → **Create and Continue** → **Done**.
3. Yaratilgan service account ustiga bosing → **Keys** bo'limi → **Add Key → Create new key**.
4. **JSON** ni tanlang → **Create**. Fayl kompyuteringizga yuklab olinadi.
5. Service account **email**'ini nusxalab oling — `...@...iam.gserviceaccount.com` ko'rinishida (keyingi qadamda kerak).

## 4. JSON faylni loyihaga qo'yish

```bash
cd ~/bot
mkdir -p secrets
# yuklab olingan faylni shu yerga ko'chiring:
#   secrets/service_account.json
```

## 5. Google Sheets jadval yaratish va ulashish

1. [sheets.new](https://sheets.new) — yangi bo'sh jadval yarating.
2. **Share** (Ulashish) tugmasi → 3-qadamdagi service account **email**'ini qo'shing → **Editor** huquqi bering → **Send**.
   > Bu juda muhim — busiz bot jadvalga yoza olmaydi!
3. Jadval URL'idan **ID** ni oling:
   `https://docs.google.com/spreadsheets/d/`**`SHU_QISM_ID`**`/edit`

## 6. `.env` ni to'ldirish

```env
GOOGLE_SHEETS_CREDENTIALS=/secrets/service_account.json
GOOGLE_SPREADSHEET_ID=SHU_QISM_ID
SHEETS_SYNC_INTERVAL_MIN=10
```

## 7. Ishga tushirish

```bash
docker compose up -d --build
```

Bot loglarida `Sheets ikki tomonlama sync jadvali yoqildi` ko'rinadi.

## 8. Sinash

- Telegram'da `/admin` → **🔄 Sheets'ni yangilash** → jadvalda **Users / Codes / Bonuses / Hisobot** varaqlari paydo bo'ladi.
- Jadvaldagi **Codes** varag'ida yangi qatorga ruchka kodi yozing (A ustun) → yana **🔄 Sheets'ni yangilash** bosing → kod DB'ga qo'shiladi.
- **Bonuses** varag'ida A ustunga bonus kodi, B ustunga foiz (masalan 10) yozsangiz — DB'ga qo'shiladi.

---

## ⚙️ Qanday ishlaydi (muhim)

| Amal | Natija |
|---|---|
| Sheets'da yangi kod yozdingiz | Keyingi sync'da DB'ga qo'shiladi (dublikat bo'lsa o'tkazib yuboriladi) |
| DB'da o'zgarish bo'ldi (bot orqali) | Keyingi sync'da Sheets yangilanadi |
| Status o'zgartirish | Sheets'da emas, `/admin` panel orqali qiling (Sheets eksportda qayta yoziladi) |

> ⚠️ **Eslatma:** Sheets'dan faqat **yangi kod/bonus qo'shiladi**. Status o'zgartirish va bloklash uchun `/admin` paneldan foydalaning. DB — asosiy haqiqat manbai, Sheets esa "kirish + ko'rish" oynasi.

## Xavfsizlik
- `secrets/` papkasi `.gitignore`'da — JSON kalit GitHub'ga ketmaydi.
- Service account faqat shu bitta jadvalga kirish huquqiga ega.
