import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from config import GEMINI_API_KEY

# Gemini API sozlamalari
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Modelni tanlash
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "Siz talabaning shaxsiy aqlli yordamchisisiz. "
        "Talabaning dars jadvali, baholari va HEMIS ma'lumotlari bo'yicha berilgan "
        "savollariga aniq, xushmuomala va o'zbek tilida yordam bering."
    )
)

async def ask_gemini(prompt: str, context: str = "") -> str:
    """Gemini AI ga asinxron so'rov yuborish va javob olish."""
    try:
        if context:
            full_prompt = f"Talaba ma'lumotlari va kontekst:\n{context}\n\nFoydalanuvchi savoli: {prompt}"
        else:
            full_prompt = prompt

        # Asinxron chaqiruv
        response = await model.generate_content_async(full_prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API xatosi: {e}")
        