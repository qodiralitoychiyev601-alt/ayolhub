# AyolHub AI — Guliston

**1 ta bot + 1 ta guruh.** Matn, rasm, video, ovozli murojaatlar shu yagona
guruhga tushadi. AI maslahatchi ulangan (Gemini, bepul tarif). Loyiha
GitHub + Railway orqali joylashtirishga tayyor.

---

## A-QISM: Local'da sinab ko'rish (Railway'ga joylashtirishdan oldin)

### 1. Python o'rnatish
https://www.python.org/downloads/ — "Add Python to PATH" ni belgilang (Windows).

### 2. Loyihani tayyorlash
```bash
cd ayolhub_bot
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. .env faylini to'ldirish
`.env.example` dan nusxa oling, nomini `.env` deb o'zgartiring:

```
BOT_TOKEN=BotFather'dan olgan tokeningiz
GROUP_ID=guruhingiz ID (get_chat_id.py orqali oling)
GEMINI_API_KEY=https://aistudio.google.com/app/apikey dan bepul kalit
```

### 4. Ishga tushirish va sinash
```bash
python run.py
```
`/start`, murojaat yuborish, AI maslahatchi — barchasini sinab ko'ring.
Hammasi ishlasa, B-qismga o'ting.

---

## B-QISM: GitHub'ga joylash

### 1. GitHub'da repository yaratish
1. https://github.com → "New repository" → nom bering (masalan `ayolhub-bot`)
2. **Private** qilib qo'ying (kod ichida maxfiy narsa yo'q, lekin xavfsizroq)
3. "Create repository" bosing

### 2. Kodni yuklash
Loyiha papkasida terminalda:

```bash
git init
git add .
git commit -m "Boshlang'ich versiya"
git branch -M main
git remote add origin https://github.com/FOYDALANUVCHI_NOMI/ayolhub-bot.git
git push -u origin main
```

> ⚠️ `.env` fayli **hech qachon** GitHub'ga yuklanmaydi — `.gitignore` buni
> avtomatik oldini oladi. Tokeningiz xavfsiz qoladi.

---

## C-QISM: Railway'ga joylash

### 1. Railway'da loyiha yaratish
1. https://railway.app → GitHub hisobingiz bilan kiring
2. "New Project" → **"Deploy from GitHub repo"**
3. `ayolhub-bot` repositoriyangizni tanlang
4. Railway avtomatik `Procfile` va `railway.json`ni aniqlab, Python loyihasi
   ekanini tushunadi va build qiladi

### 2. Environment Variables (maxfiy sozlamalar) qo'shish
Railway loyihangiz sahifasida **Variables** bo'limiga o'ting va qo'shing:

| Nomi | Qiymati |
|---|---|
| `BOT_TOKEN` | BotFather tokeningiz |
| `GROUP_ID` | guruh ID (masalan `-5294442174`) |
| `GEMINI_API_KEY` | Gemini API kalitingiz |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/ayolhub.db` (pastga qarang — Volume kerak) |
| `TRACKING_PREFIX` | `GLS` |

### 3. Volume qo'shish (MA'LUMOTLAR YO'QOLMASLIGI UCHUN SHART)

Railway'da har deploy qilinganda fayl tizimi tozalanadi — agar Volume
ulanmasa, har safar kod yangilanganda **bazangiz o'chib ketadi**.

1. Railway loyihangizda **"+ New"** → **"Volume"**
2. Mount path: `/data`
3. Yuqoridagi `DATABASE_URL` qiymatini xuddi shunday qoldiring:
   `sqlite+aiosqlite:////data/ayolhub.db`

Bu bazani doimiy saqlaydi, har deploy'da yo'qolmaydi.

> **Muqobil (tavsiya etiladi, agar murojaatlar soni ko'payib borsa):**
> Railway'da "+ New" → "Database" → "PostgreSQL" qo'shing, u avtomatik
> `DATABASE_URL` beradi (masalan `postgresql://...`). Shunda faqat
> `DATABASE_URL`ni `postgresql+asyncpg://...` ga almashtirib, `requirements.txt`ga
> `asyncpg==0.30.0` qo'shib qo'yasiz — boshqa hech narsa o'zgartirilmaydi,
> chunki loyiha Repository Pattern bilan yozilgan.

### 4. Deploy
Yuqoridagilarni sozlagach, Railway avtomatik deploy qiladi. **Deployments**
bo'limida loglarni kuzating — `bot_starting` yozuvi chiqsa, bot ishlayapti.

### 5. Tekshirish
Telegram'da botga `/start` yuboring, murojaat yuboring, guruhda kartani
tekshiring.

---

## Keyingi safar kod yangilashda

Kod ustida ishlaganingizda, o'zgarishlarni push qilishning o'zi yetarli —
Railway avtomatik qayta deploy qiladi:

```bash
git add .
git commit -m "O'zgarish tavsifi"
git push
```

---

## Xavfsizlik eslatmasi

- `BOT_TOKEN`ni hech qachon ochiq joyda (chat, forum, kodga hardcoded holda)
  ulashmang. Agar tasodifan oshkor bo'lsa, @BotFather → `/mybots` → botingiz
  → "API Token" → "Revoke current token" orqali darhol yangilang.
- `.env` fayli faqat sizning kompyuteringizda va Railway'ning Variables
  bo'limida turadi — GitHub'da hech qachon ko'rinmaydi.

---

## Loyiha strukturasi

```
ayolhub_bot/
├── Procfile                    # Railway: qaysi buyruq bilan ishga tushirish
├── railway.json                 # Railway build/deploy sozlamalari
├── .python-version              # Python versiyasini qat'iylashtirish
├── app/
│   ├── config.py                 # .env / Railway Variables dan sozlamalar
│   ├── constants.py               # 22 mahalla nomlari
│   ├── bot.py                      # Bot va router'larni yig'adi
│   ├── database/                    # Modellar, session
│   ├── repositories/                 # DB bilan ishlash qatlami
│   ├── services/                      # Biznes mantiq + AI xizmati
│   ├── handlers/                       # Telegram xabarlarini qabul qiladi
│   ├── keyboards/, states/, middlewares/
├── run.py                        # Kirish nuqtasi
├── get_chat_id.py                # Guruh ID sini bilish uchun yordamchi
└── .env.example                  # Namuna (haqiqiy qiymatlarsiz)
```

## Keyingi modul

Railway'da barqaror ishlayotganini tasdiqlagach, keyingi navbatda:
- 💼 Ish o'rinlari / 🎓 Kurslar / 💰 Grantlar — real kontent
- Operator statistikasi (necha murojaat, o'rtacha javob vaqti)
- PostgreSQL'ga o'tish (agar murojaatlar soni ko'paysa)
