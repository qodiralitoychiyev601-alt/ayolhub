"""
Bytez orqali ishlaydigan AI maslahatchi xizmati.

MUHIM: Google Gemini'ning ushbu loyihaga bog'langan hisobida "AQ." formatidagi
kalitlar standart REST API (generativelanguage.googleapis.com) bilan
ishlamasligi aniqlandi — bu Google'ning o'zida davom etayotgan, hisobga xos
muammo (401 ACCESS_TOKEN_TYPE_UNSUPPORTED). Shu sababli AI provayder sifatida
Bytez (bytez.com) ga o'tildi — bitta API kalit orqali ko'plab modellarga
(shu jumladan ochiq manba modellariga) ulanish imkonini beradi.

Bu qatlam Telegram'dan mustaqil — kelajakda boshqa provayder (masalan, Gemini
muammosi tuzatilsa) qo'shilsa ham shu fayl almashadi, handler'lar o'zgarmaydi.
"""

import httpx

from app.config import get_settings

settings = get_settings()

BYTEZ_URL_TEMPLATE = "https://api.bytez.com/models/v2/{model}"

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


def _extract_text(output) -> str:
    """Bytez javobi model turiga qarab {"role":..,"content":..} yoki oddiy
    matn ko'rinishida kelishi mumkin — ikkalasini ham qo'llab-quvvatlaymiz."""
    if isinstance(output, dict):
        return str(output.get("content") or "").strip()
    if isinstance(output, str):
        return output.strip()
    return ""


async def ask_ai(user_message: str) -> str:
    """Foydalanuvchi xabariga Bytez orqali javob qaytaradi."""
    if not settings.BYTEZ_API_KEY:
        return (
            "🤖 AI maslahatchi hozircha sozlanmagan. "
            "Administrator BYTEZ_API_KEY ni Railway Variables'ga qo'shishi kerak."
        )

    url = BYTEZ_URL_TEMPLATE.format(model=settings.BYTEZ_MODEL)
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "params": {"temperature": 0.6, "max_length": 500},
    }
    headers = {
        "Authorization": settings.BYTEZ_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        if data.get("error"):
            # Bytez xatoni 200 status bilan ham "error" maydonida qaytarishi
            # mumkin (masalan model band bo'lsa) — shuni ham tekshiramiz.
            print(f"[ai_service] Bytez 'error' maydoni bilan qaytardi: {data['error']!r}")
            return "Kechirasiz, AI xizmatiga ulanishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

        text = _extract_text(data.get("output"))
        if not text:
            print(f"[ai_service] Bytez bo'sh/kutilmagan javob qaytardi: data={data!r}")
            return "Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

        return text

    except httpx.HTTPStatusError as exc:
        # MUHIM: xato sababini Railway loglariga chiqaramiz (foydalanuvchiga
        # emas!). Shu qatorsiz nima uchun ishlamayotganini bilib bo'lmaydi.
        body_preview = exc.response.text[:500]
        print(
            f"[ai_service] Bytez HTTP xatosi: status={exc.response.status_code} "
            f"model={settings.BYTEZ_MODEL} body={body_preview!r}"
        )
        if exc.response.status_code in (401, 403):
            return (
                "Kechirasiz, AI xizmati sozlamalarida muammo bor "
                "(API kalit noto'g'ri yoki ruxsat yo'q). Administratorga xabar berildi."
            )
        if exc.response.status_code == 429:
            return (
                "Hozir AI xizmatiga so'rovlar juda ko'p yoki kredit yetarli emas. "
                "Iltimos, bir necha daqiqadan so'ng qayta urinib ko'ring."
            )
        return "Kechirasiz, AI xizmatiga ulanishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

    except (KeyError, ValueError, TypeError) as exc:
        print(f"[ai_service] Bytez javobini o'qishda xatolik: {exc!r}")
        return "Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

    except httpx.RequestError as exc:
        print(f"[ai_service] Bytez'ga ulanishda tarmoq xatosi: {exc!r}")
        return "Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."
