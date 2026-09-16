import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# Config fayldan tokenni chaqiramiz
from config import BOT_TOKEN 
from services.gemini_service import ask_gemini
from services.claude_service import ask_claude_for_ppt

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Assalomu alaykum! Men sizning maxsus gibrid botingizman.\n\n"
        "⚡️ Oddiy savollarni yozsangiz — **Gemini** tezkor javob beradi.\n"
        "📊 `/ppt [mavzu]` deb yozsangiz — **Claude** sizga chiroyli taqdimot tayyorlaydi."
    )

@dp.message(Command("ppt"))
async def ppt_handler(message: Message):
    mavzu = message.text.replace("/ppt", "").strip()
    if not mavzu:
        await message.answer("Iltimos, mavzuni kiriting. Masalan: `/ppt O'zbekiston vatanim mening`", parse_mode="Markdown")
        return
    
    kutilish_xabari = await message.answer("⏳ Claude taqdimot ma'lumotlarini chuqur tahlil qilmoqda... Iltimos kuting.")
    
    # Katta vazifani Claude'ga yuboramiz
    claude_javobi = await ask_claude_for_ppt(mavzu)
    
    await kutilish_xabari.delete()
    await message.answer(f"📊 **Taqdimot tayyor (Claude 3.5):**\n\n{claude_javobi}")

@dp.message()
async def general_text_handler(message: Message):
    kutilish_xabari = await message.answer("💬 Gemini o'ylamoqda...")
    
    # Kundalik savollarni Gemini'ga yuboramiz
    gemini_javobi = await ask_gemini(message.text)
    
    await kutilish_xabari.delete()
    await message.answer(gemini_javobi)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
