"""
Google Gemini bilan ishlaydigan AI maslahatchi xizmati.

Gemini bepul tarifidan foydalanamiz (Google AI Studio orqali API kalit
olinadi, kredit karta shart emas). Bu qatlam Telegram'dan mustaqil —
kelajakda web-panel yoki boshqa AI provayder qo'shilsa ham shu fayl
almashadi, handler'lar o'zgarmaydi.
"""

import httpx

from app.config import get_settings

settings = get_settings()

GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

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
    "3-5 gapdan oshmasin, imkon qadar qisqa va aniq bo'lsin."
)


async def ask_ai(user_message: str) -> str:
    """Foydalanuvchi xabariga Gemini orqali javob qaytaradi."""
    if not settings.GEMINI_API_KEY:
        return (
            "🤖 AI maslahatchi hozircha sozlanmagan. "
            "Administrator GEMINI_API_KEY ni Railway Variables'ga qo'shishi kerak."
        )

    url = GEMINI_URL_TEMPLATE.format(model=settings.GEMINI_MODEL)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 500},
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url, params={"key": settings.GEMINI_API_KEY}, json=payload
            )
            response.raise_for_status()
            data = response.json()

        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    except httpx.HTTPStatusError as exc:
        # MUHIM: xato sababini Railway loglariga chiqaramiz (foydalanuvchiga
        # emas!). Shu qatorsiz, nima uchun ishlamayotganini hech qachon
        # bilib bo'lmas edi — status kodi va Google'ning javobi endi
        # `railway logs` orqali ko'rinadi.
        body_preview = exc.response.text[:500]
        print(
            f"[ai_service] Gemini HTTP xatosi: status={exc.response.status_code} "
            f"model={settings.GEMINI_MODEL} body={body_preview!r}"
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
        return "Kechirasiz, AI xizmatiga ulanishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

    except (KeyError, IndexError) as exc:
        print(f"[ai_service] Gemini javobini o'qishda xatolik: {exc!r} | data={data!r}")
        return "Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

    except httpx.RequestError as exc:
        print(f"[ai_service] Gemini'ga ulanishda tarmoq xatosi: {exc!r}")
        return "Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."
