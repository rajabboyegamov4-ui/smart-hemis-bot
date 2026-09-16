import aiohttp
from config import GEMINI_API_KEY

async def ask_gemini(prompt_text: str) -> str:
    """Gemini orqali oddiy savollarga javob olish (To'g'rilangan REST API usuli)"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    data = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "system_instruction": {
            "parts": [{"text": "Siz islomshunoslik fakulteti talabasining shaxsiy yordamchisisiz. Qisqa, aniq va kundalik vazifalarda tezkor foydali javob bering."}]
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=15) as response:
                if response.status == 200:
                    result = await response.json()
                    # Xavfsiz tarzda javobni ajratib olish
                    candidates = result.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            return parts[0].get('text', 'Javob topilmadi.')
                    return "Bo'sh javob keldi."
                else:
                    error_info = await response.text()
                    return f"❌ Gemini API xatosi ({response.status}): {error_info}"
    except Exception as e:
        return f"❌ Server ulanishida xatolik: {str(e)}"
