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
import base64

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


GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


async def transcribe_voice(audio_bytes: bytes, filename: str = "voice.ogg") -> str | None:
    """Ovozli xabarni Groq Whisper (whisper-large-v3) orqali matnga aylantiradi.

    Xato bo'lsa (yoki kalit yo'q bo'lsa) None qaytaradi — chaqiruvchi tomon
    buni "tushunmadim" degan tabiiy xabarga aylantiradi."""
    if not settings.GROQ_API_KEY:
        return None

    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    files = {"file": (filename, audio_bytes)}
    data = {"model": "whisper-large-v3", "language": "uz"}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                GROQ_TRANSCRIBE_URL, headers=headers, data=data, files=files
            )
            response.raise_for_status()
            result = response.json()

        text = (result.get("text") or "").strip()
        return text or None

    except httpx.HTTPStatusError as exc:
        print(
            f"[ai_service] Groq transkripsiya xatosi: status={exc.response.status_code} "
            f"body={exc.response.text[:300]!r}"
        )
        return None
    except (KeyError, ValueError, TypeError) as exc:
        print(f"[ai_service] Groq transkripsiya javobini o'qishda xatolik: {exc!r}")
        return None
    except httpx.RequestError as exc:
        print(f"[ai_service] Groq transkripsiya tarmoq xatosi: {exc!r}")
        return None


GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


async def ask_ai_with_image(user_text: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Rasmni (va ixtiyoriy matnli savolni) Groq'ning vision modeliga yuborib,
    tahlil/javob oladi. Model rasm ichidagi matnni ham o'qiy oladi (masalan
    hujjat, spravka, chek va h.k.), shuning uchun bu funksiya rasm orqali
    yuborilgan hujjatlarni ham tushuntirib berishi mumkin."""
    if not settings.GROQ_API_KEY:
        return (
            "🤖 AI maslahatchi hozircha sozlanmagan. "
            "Administrator GROQ_API_KEY ni Railway Variables'ga qo'shishi kerak."
        )

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64_image}"

    prompt_text = (user_text or "").strip() or (
        "Bu rasmda nima tasvirlangan yoki yozilgan? Agar bu hujjat, spravka "
        "yoki qog'oz bo'lsa, mazmunini o'zbek tilida tushuntirib ber va agar "
        "kerak bo'lsa tegishli maslahat ham qo'sh."
    )

    payload = {
        "model": GROQ_VISION_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "temperature": 0.6,
        "max_tokens": 700,
    }
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(GROQ_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        text = (data["choices"][0]["message"]["content"] or "").strip()
        if not text:
            print(f"[ai_service] Groq vision bo'sh javob qaytardi: data={data!r}")
            return "Kechirasiz, rasmni tahlil qilishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

        return text

    except httpx.HTTPStatusError as exc:
        body_preview = exc.response.text[:500]
        print(
            f"[ai_service] Groq vision HTTP xatosi: status={exc.response.status_code} "
            f"body={body_preview!r}"
        )
        if exc.response.status_code in (401, 403):
            return "Kechirasiz, AI xizmati sozlamalarida muammo bor. Administratorga xabar berildi."
        if exc.response.status_code == 429:
            return "Hozir AI xizmatiga so'rovlar juda ko'p. Iltimos, birozdan so'ng qayta urinib ko'ring."
        return "Kechirasiz, rasmni tahlil qilishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

    except (KeyError, IndexError, ValueError, TypeError) as exc:
        print(f"[ai_service] Groq vision javobini o'qishda xatolik: {exc!r}")
        return "Kechirasiz, rasmni tahlil qilishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."

    except httpx.RequestError as exc:
        print(f"[ai_service] Groq vision tarmoq xatosi: {exc!r}")
        return "Kechirasiz, rasmni tahlil qilishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."


MAX_PDF_CHARS = 15000  # juda uzun PDF'lar uchun cheklov (token/tezlik uchun)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """PDF'dan matnni ajratib oladi. Agar PDF skanerlangan rasm bo'lsa (matn
    qatlami bo'lmasa), bo'sh satr qaytaradi — chaqiruvchi buni foydalanuvchiga
    tushuntiradi (masalan, rasm sifatida yuborishni tavsiya qiladi)."""
    from pypdf import PdfReader
    from io import BytesIO

    reader = PdfReader(BytesIO(pdf_bytes))
    parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(page_text.strip())

    full_text = "\n\n".join(parts).strip()
    if len(full_text) > MAX_PDF_CHARS:
        full_text = full_text[:MAX_PDF_CHARS] + "\n\n[…matn uzun bo'lgani uchun qisqartirildi…]"
    return full_text


async def ask_ai_about_pdf(user_text: str, pdf_text: str) -> str:
    """PDF'dan ajratilgan matnni foydalanuvchi savoli bilan birga AI'ga
    yuboradi. Oddiy ask_ai() dan foydalanamiz — faqat kontekstga PDF matnini
    qo'shib beramiz."""
    question = (user_text or "").strip() or "Ushbu hujjat mazmunini tushuntirib ber va agar kerak bo'lsa maslahat ber."
    combined = (
        f"Foydalanuvchi PDF fayl yubordi. Hujjat matni:\n\n{pdf_text}\n\n"
        f"Foydalanuvchining savoli: {question}"
    )
    return await ask_ai(combined)
