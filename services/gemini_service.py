import aiohttp
from config import GEMINI_API_KEY

async def ask_gemini(prompt_text: str) -> str:
    """Gemini orqali oddiy savollarga javob olish (Raw REST API usuli)"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "systemInstruction": {
            "parts": [{"text": "Siz islomshunoslik fakulteti talabasining shaxsiy yordamchisisiz. Qisqa, aniq va kundalik vazifalarda tezkor foydali javob bering."}]
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                error_info = await response.text()
                return f"Gemini tizimida xatolik: {error_info}"
