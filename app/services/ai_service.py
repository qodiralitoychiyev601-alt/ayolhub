"""
Groq orqali ishlaydigan AI maslahatchi xizmati.

TARIX: Avval Google Gemini ishlatilgan, lekin loyihaga bog'langan Google
hisobida "AQ." formatidagi kalitlar standart REST API bilan ishlamadi
(Google'ning o'zida davom etayotgan muammo). Keyin Bytez sinovdan
o'tkazildi (pullik). Yakuniy yechim — Groq: doimiy BEPUL tarif,
OpenAI-mos standart format, kreditkarta shart emas.

Bu qatlam Telegram'dan mustaqil — kelajakda boshqa provayder qo'shilsa
ham shu fayl almashadi, handler'lar o'zgarmaydi.
"""

import httpx

from app.config import get_settings

settings = get_settings()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "Sen 'AyolHub AI' — Guliston tumani Oila va xotin-qizlar bo'limining "
    "sun'iy intellekt maslahatchisisan. Ayollar, oilalar va fuqarolarga "
    "quyidagi mavzularda o'zbek tilida sodda, qisqa va tushunarli maslahat "
    "berasan: huquqiy savollar, oilaviy munosabatlar, psixologik yordam, "
    "ish topish, grant va subsidiyalar, tadbirkorlik. Har doim mehribon, "
    "hurmatli va professional ohangda javob ber. Agar savol shoshilinch "
    "xavf (zo'ravonlik, o'z joniga qasd qilish va h.k.) haqida bo'lsa, "
    "darhol operatorlar bilan bog'lanishni va 102 raqamiga qo'ng'iroq "
    "qilishni tavsiya qil. Sen shifokor yoki advokat emassan — murakkab "
    "holatlarda doim mutaxassisga murojaat qilishni maslahat ber. Javoblaring "
    "3-5 gapdan oshmasin, imkon qadar qisqa va aniq bo'lsin. Faqat o'zbek "
    "tilida javob ber."
)


async def ask_ai(user_message: str) -> str:
    """Foydalanuvchi xabariga Groq (OpenAI-mos) orqali javob qaytaradi."""
    if not settings.GROQ_API_KEY:
        return (
            "🤖 AI maslahatchi hozircha sozlanmagan. "
            "Administrator GROQ_API_KEY ni Railway Variables'ga qo'shishi kerak."
        )

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.6,
        "max_tokens": 500,
    }
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(GROQ_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        text = data["choices"][0]["message"]["content"]
        text = (text or "").strip()
        if not text:
            print(f"[ai_service] Groq bo'sh javob qaytardi: data={data!r}")
            return "Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

        return text

    except httpx.HTTPStatusError as exc:
        # MUHIM: xato sababini Railway loglariga chiqaramiz (foydalanuvchiga
        # emas!). Shu qatorsiz nima uchun ishlamayotganini bilib bo'lmaydi.
        body_preview = exc.response.text[:500]
        print(
            f"[ai_service] Groq HTTP xatosi: status={exc.response.status_code} "
            f"model={settings.GROQ_MODEL} body={body_preview!r}"
        )
        if exc.response.status_code in (401, 403):
            return (
                "Kechirasiz, AI xizmati sozlamalarida muammo bor "
                "(API kalit noto'g'ri yoki ruxsat yo'q). Administratorga xabar berildi."
            )
        if exc.response.status_code == 429:
            return (
                "Hozir AI xizmatiga so'rovlar juda ko'p. Iltimos, bir necha "
                "daqiqadan so'ng qayta urinib ko'ring."
            )
        if exc.response.status_code == 404:
            return (
                "Kechirasiz, AI xizmati sozlamalarida muammo bor "
                "(model nomi noto'g'ri). Administratorga xabar berildi."
            )
        return "Kechirasiz, AI xizmatiga ulanishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

    except (KeyError, IndexError, ValueError, TypeError) as exc:
        print(f"[ai_service] Groq javobini o'qishda xatolik: {exc!r}")
        return "Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

    except httpx.RequestError as exc:
        print(f"[ai_service] Groq'ga ulanishda tarmoq xatosi: {exc!r}")
        return "Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."
