import os
import asyncio
import warnings
import requests
warnings.filterwarnings("ignore")
import google.generativeai as genai
from dotenv import load_dotenv
import database

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini zaxira sifatida sozlanadi
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """Sen do'konning "Abdulloh" ismli maslahatchi botisan.
Mijozlar senga har xil texnika va gadjetlar borasida savollar bilan yuzlanishadi.
Sen ularga do'stona, xushmuomala tarzda o'zbek tilida javob berishing kerak.
Mijoz mahsulot narxi yoki u haqida ma'lumot so'rasa, senga berilgan mahsulotlar bazasidan qidirib topib, faqat to'g'ri narx va ma'lumotlarni ayt. Bazada yo'q mahsulotni o'zingdan to'qib aytma!
Agar mijoz qidirayotgan mahsulot bazada bo'lmasa, uni sotuvda yo'qligini xushmuomalalik bilan tushuntir.
Sening javoblaring qisqa, aniq va foydali bo'lishi kerak."""


def _groq_sync_request(messages: list) -> str:
    """Sinxron Groq HTTP so'rovi (to_thread orqali chaqiriladi)."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 1024,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _gemini_sync_request(full_prompt: str) -> str:
    """Sinxron Gemini so'rovi (to_thread orqali chaqiriladi)."""
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.5,
            "top_p": 0.95,
            "max_output_tokens": 1024,
        },
    )
    response = model.generate_content(full_prompt)
    return response.text


async def get_agent_response(user_message: str, history: list = None) -> str:
    """
    Foydalanuvchi xabariga async tarzda AI javobi qaytaradi.
    history — oldingi xabarlar ro'yxati: [{"role": "user/assistant", "content": "..."}]
    """
    catalog_info = database.get_all_products_info()
    system_with_catalog = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Hozirda ombordagi mahsulotlar:\n{catalog_info}"
    )

    # Groq uchun to'liq xabarlar ro'yxatini tuzamiz (tarix bilan)
    messages = [{"role": "system", "content": system_with_catalog}]
    if history:
        messages.extend(history[-10:])  # oxirgi 10 ta xabar (token tejash)
    messages.append({"role": "user", "content": user_message})

    # 1. Groq (asosiy) — asyncio.to_thread bilan blocking bo'lmasin
    if GROQ_API_KEY:
        try:
            print(f"[Groq] So'rov yuborilmoqda...")
            result = await asyncio.to_thread(_groq_sync_request, messages)
            print(f"[Groq] Javob olindi.")
            return result
        except Exception as e:
            print(f"[Groq] Xatolik: {e} — Gemini zaxiraga o'tilmoqda...")

    # 2. Gemini (zaxira)
    if GEMINI_API_KEY:
        try:
            print(f"[Gemini] So'rov yuborilmoqda (zaxira)...")
            full_prompt = (
                f"{system_with_catalog}\n\n"
                f"Mijoz xabari: {user_message}\n\nJavobingni yoz:"
            )
            result = await asyncio.to_thread(_gemini_sync_request, full_prompt)
            print(f"[Gemini] Javob olindi.")
            return result
        except Exception as e:
            print(f"[Gemini] Xatolik: {e}")

    # 3. Oddiy qidiruv (oxirgi chora)
    return database.search_product(user_message)
