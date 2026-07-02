"""Botning barcha matnlari (TZ §13 uslubi: sodda, muloyim, kam emoji).

Kelajakda ko'p tillilik uchun shu modul i18n bilan almashtiriladi (TZ §11.2).
"""

# ── Start / registratsiya ──
START = (
    "Assalomu alaykum!\n"
    "Aqlli ruchka va interaktiv kitoblarimiz botiga xush kelibsiz.\n\n"
    "Bot orqali siz:\n"
    "• mahsulot haqida video ko‘rishingiz;\n"
    "• mahsulot haqida batafsil ma’lumot olishingiz;\n"
    "• sotuv kanallarimizga o‘tishingiz;\n"
    "• xaridingizni tasdiqlab, keyingi kitoblar uchun bir martalik 10% bonus "
    "olishingiz mumkin.\n\n"
    "Davom etish uchun ismingizni kiriting."
)
ASK_NAME_AGAIN = "Iltimos, ismingizni to‘g‘ri kiriting (kamida 2 ta harf)."
ASK_PHONE = (
    "Rahmat! Endi telefon raqamingizni yuboring.\n\n"
    "Pastdagi “📱 Raqamni yuborish” tugmasini bosing yoki raqamni qo‘lda kiriting."
)
ASK_PHONE_AGAIN = (
    "Telefon raqami noto‘g‘ri ko‘rinadi.\n"
    "Iltimos, +998 formatida kiriting yoki tugma orqali yuboring."
)
REGISTERED = "Tayyor! Asosiy menyudan kerakli bo‘limni tanlang. 👇"

# ── Asosiy menyu ──
MAIN_MENU = "Asosiy menyu. Kerakli bo‘limni tanlang. 👇"

# ── Video (TZ §5) ──
VIDEO_CAPTION = (
    "🎬 Aqlli ruchka bolalarga o‘qish, tinglash, talaffuz qilish va yangi "
    "so‘zlarni o‘rganishda yordam beradi.\n\n"
    "Mahsulotni xarid qilish uchun quyidagi tugmalardan birini tanlang."
)
VIDEO_MISSING = (
    "🎬 Video tez orada qo‘shiladi.\n"
    "Mahsulot haqida ma’lumot olish yoki xarid qilish uchun quyidagi tugmalardan foydalaning."
)

# ── Mahsulot ma'lumoti (TZ §6) ──
PRODUCT_INFO = (
    "📖 Aqlli ruchka — bu bolalar uchun interaktiv o‘quv qurilmasi.\n\n"
    "U OID texnologiyasi asosida ishlaydi. Bola ruchkani kitobdagi rasm, matn "
    "yoki belgiga tekkizganda ruchka ovoz chiqaradi.\n\n"
    "Mahsulot quyidagilarga yordam beradi:\n"
    "• so‘z boyligini oshirish;\n"
    "• ingliz va rus tillarini o‘rganish;\n"
    "• talaffuzni yaxshilash;\n"
    "• eshitish va ko‘rish orqali o‘rganish;\n"
    "• mustaqil o‘qishga qiziqish uyg‘otish;\n"
    "• mantiqiy fikrlashni rivojlantirish."
)

# ── Sotuv kanallari (TZ §7) ──
CHANNELS = (
    "🛒 Mahsulotni quyidagi kanallar orqali xarid qilishingiz mumkin.\n"
    "Kerakli kanalni tanlang va buyurtma bering."
)

# ── Bonus oqimi (TZ §8) ──
ASK_CODE = (
    "🎁 Keyingi kitoblar uchun 10% bonus olish uchun aqlli ruchka orqasidagi "
    "maxsus kodni kiriting.\n\n"
    "Masalan: ABC12345"
)
CODE_EMPTY = "Kod bo‘sh bo‘lishi mumkin emas. Iltimos, kodni kiriting."

def bonus_success(bonus_code: str, percent: int = 10) -> str:
    return (
        "🎉 Tabriklaymiz! Xaridingiz tasdiqlandi.\n\n"
        f"Sizga keyingi kitoblar xaridi uchun bir martalik {percent}% bonus taqdim qilindi.\n\n"
        f"Sizning bonus kodingiz: {bonus_code}\n\n"
        "Ushbu bonusdan keyingi kitoblar xaridida foydalanishingiz mumkin.\n"
        "Bonusdan foydalanish uchun operatorga murojaat qiling yoki sotuv "
        "kanalimiz orqali buyurtma bering."
    )

CONFIRMED_NO_BONUS = (
    "✅ Xaridingiz tasdiqlandi.\n\n"
    "Hozirda avtomatik bonus kodlar bazasida mavjud bonus qolmagan. "
    "Iltimos, operator bilan bog‘laning — sizga bir martalik 10% bonus qo‘lda "
    "taqdim qilinadi."
)
CODE_NOT_FOUND = (
    "❌ Kiritilgan kod topilmadi.\n\n"
    "Iltimos, ruchka orqasidagi kodni diqqat bilan tekshirib, qayta kiriting.\n"
    "Agar muammo davom etsa, operator bilan bog‘laning."
)
CODE_ALREADY_USED = (
    "⚠️ Bu kod avval aktivlashtirilgan.\n\n"
    "Agar siz bu kodni birinchi marta kiritayotgan bo‘lsangiz, iltimos operator "
    "bilan bog‘laning."
)
CODE_BLOCKED = (
    "🚫 Bu kod orqali bonus olish imkoniyati mavjud emas.\n\n"
    "Iltimos, batafsil ma’lumot uchun operator bilan bog‘laning."
)

def rate_limited(minutes: int) -> str:
    return (
        "⛔️ Siz juda ko‘p marta noto‘g‘ri kod kiritdingiz.\n"
        f"Iltimos, {minutes} daqiqadan so‘ng qayta urinib ko‘ring yoki operator "
        "bilan bog‘laning."
    )

BONUS_USAGE = (
    "Bonusdan foydalanish uchun bonus kodingizni operatorga yoki sotuv kanaliga "
    "buyurtma berishda ayting. Bonus bir martalik."
)

# ── Kitoblar ──
BOOKS_INTRO = (
    "📚 Kitoblar bo‘limi.\n\n"
    "Kerakli kitobni tanlang. Kitobni yuklab olish uchun aqlli ruchka "
    "orqasidagi maxsus kodni kiritishingiz kerak bo‘ladi."
)
BOOKS_EMPTY = (
    "📚 Hozircha kitoblar qo‘shilmagan.\n"
    "Tez orada kitoblar shu yerda paydo bo‘ladi."
)

def book_ask_code(title: str) -> str:
    return (
        f"📖 «{title}» kitobini yuklab olish uchun aqlli ruchka orqasidagi "
        "maxsus kodni kiriting.\n\n"
        "Masalan: ABC12345"
    )

def book_sending(title: str) -> str:
    return f"✅ Kod to‘g‘ri! «{title}» yuborilmoqda..."

BOOK_CODE_INVALID = (
    "❌ Kod noto‘g‘ri yoki topilmadi.\n"
    "Iltimos, ruchka orqasidagi kodni tekshirib, qayta kiriting."
)
BOOK_NOT_FOUND = "Bu kitob hozircha mavjud emas."
BOOK_FILE_MISSING = (
    "Kechirasiz, kitob fayli topilmadi. Iltimos, operator bilan bog‘laning."
)


# ── FAQ (TZ §11.1) ──
FAQ = (
    "❓ Ko‘p beriladigan savollar:\n\n"
    "1. Aqlli ruchka qanday ishlaydi?\n"
    "Ruchkani kitobdagi rasm yoki matnga tekkizsangiz, u ovoz chiqaradi.\n\n"
    "2. Ruchka qaysi kitoblar bilan ishlaydi?\n"
    "Maxsus OID texnologiyali kitoblarimiz bilan.\n\n"
    "3. Ruchkani zaryadlash kerakmi?\n"
    "Ha, ichki akkumulyator USB orqali zaryadlanadi.\n\n"
    "4. Qanday yoshdagi bolalar uchun mos?\n"
    "Asosan 3–10 yosh bolalar uchun.\n\n"
    "5. Ruchka nechta tilni qo‘llab-quvvatlaydi?\n"
    "O‘zbek, rus va ingliz tillarini.\n\n"
    "6. 10% bonusdan qanday foydalaniladi?\n"
    "“🎁 10% bonus olish” tugmasini bosib, ruchka orqasidagi kodni kiriting.\n\n"
    "7. Ruchka orqasidagi kod qayerda joylashgan?\n"
    "Kod ruchkaning orqa qismidagi maxsus yorliqda yozilgan.\n\n"
    "Boshqa savollaringiz bo‘lsa, operator bilan bog‘laning."
)

# ── Operator (TZ §11.4) ──
def operator_text(username: str) -> str:
    return (
        "☎️ Operator bilan bog‘lanish.\n\n"
        f"Quyidagi tugma orqali operatorimizga yozing: @{username.lstrip('@')}"
    )

# ── Admin ──
ADMIN_DENIED = "Bu bo‘lim faqat administratorlar uchun."
ADMIN_MENU = "🛠 Admin panel. Amalni tanlang."

# ── Tugma yorliqlari (button labels) ──
B_VIDEO = "🎬 Mahsulot haqida video"
B_INFO = "📖 Mahsulot haqida ma’lumot"
B_BOOKS = "📚 Kitoblar"
B_CHANNELS = "🛒 Sotib olish / Sotuv kanallari"
B_BONUS = "🎁 10% bonus olish"
B_FAQ = "❓ Savol-javob"
B_OPERATOR = "☎️ Operator bilan bog‘lanish"
B_MAIN_MENU = "⬅️ Asosiy menyu"
B_LANG = "🌐 Til / Язык"

B_CH_TELEGRAM = "📨 Telegram orqali buyurtma"
B_CH_INSTAGRAM = "📷 Instagram sahifamiz"
B_CH_UZUM = "🛍 Uzum Market"
B_CH_OTHER = "🌐 Boshqa marketplace"
B_GO_CHANNEL = "➡️ Kanalga o‘tish"

B_BUY = "🛒 Sotib olish"
B_WATCH_VIDEO = "🎬 Video ko‘rish"
B_SALES_CHANNELS = "🛒 Sotuv kanallari"

B_ENTER_CODE = "✍️ Kod kiritish"
B_RETRY_CODE = "🔁 Qayta kod kiritish"
B_USE_BONUS = "🎁 Bonusdan foydalanish"

B_BOOKS_LIST = "📚 Kitoblar ro‘yxati"
B_OTHER_BOOKS = "📚 Boshqa kitoblar"

B_OPERATOR_WRITE = "✉️ Operatorga yozish"
B_SEND_PHONE = "📱 Raqamni yuborish"

CHANNEL_PICK = "Quyidagi tugma orqali tanlangan kanalga o‘ting:"
NEED_REGISTER = "Avval /start orqali ro‘yxatdan o‘ting."
