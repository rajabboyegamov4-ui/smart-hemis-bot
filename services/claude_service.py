import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config import CLAUDE_API_KEY  # .env yoki config fayldan kalitni olamiz

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

async def ask_claude(prompt: str, context: str = "") -> str:
    """Claude AI dan javob olish funksiyasi"""
    try:
        bot_vazifasi = (
            "Siz talabaning shaxsiy aqlli yordamchisiz. "
            "Talabaning dars jadvali, baholari va HEMIS ma'lumotlari bo'yicha berilgan "
            "savollariga aniq, xushmuomala va o'zbek tilida yordam bering.\n\n"
        )
        
        full_prompt = f"{bot_vazifasi}Talaba ma'lumotlari va kontekst:\n{context}\n\nFoydalanuvchi savoli: {prompt}" if context else f"{bot_vazifasi}Foydalanuvchi savoli: {prompt}"

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Eng so'nggi va kuchli modellardan biri
            max_tokens=2048,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Claude xatosi: {str(e)}"
