import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# Config fayldan tokenni chaqiramiz
from config import BOT_TOKEN 
from services.gemini_service import ask_gemini
# Claude importini hozircha o'chirib turamiz yoki kerak bo'lganda ishlatamiz

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    welcome_text = (
        "🎓 **Assalomu alaykum! Talabalarning shaxsiy aqlli yordamchisiga xush kelibsiz!**\n\n"
        "Men o'qish jarayonida sizga eng kerakli vazifalarni bajarishda yordam beraman. Nimalarga qodirman?\n\n"
        "📚 **Savol-javob:** Istalgan mavzuda (ayniqsa, islomshunoslik, tarix yoki boshqa fanlar) savol bering va aniq javob oling.\n"
        "🎓 **HEMIS Integratsiyasi:** Dars jadvali, baholar va davomatni tezda bilib oling (menyu orqali).\n"
        "📝 **Test va Konspektlar:** Menga matn yoki kitob tashlab, o'sha mavzuda testlar tuzishni yoki xulosa yozib berishni so'rashingiz mumkin.\n"
        "📊 **Taqdimotlar (/ppt):** Slaydlar uchun mukammal struktura va matnlar tayyorlash xizmati.\n\n"
        "Shunchaki o'zingizni qiziqtirgan savolni yozing va biz ishni boshlaymiz! 🚀"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(Command("ppt"))
async def ppt_handler(message: Message):
    # Bu yerda API o'rniga mijozlarni tayyorlovchi xabar chiqadi
    promo_text = (
        "🚀 **Taqdimot tayyorlash (PPT) xizmati haqida:**\n\n"
        "Ushbu funksiya dunyodagi eng kuchli **Claude 3.5 Sonnet** sun'iy intellekti asosida ishlaydi. "
        "Sizga mukammal slaydlar va taqdimot matnlarini yozib beradigan, vaqtingizni 100 barobar tejaydigan bu maxsus rejim "
        "**eng yaqin fursatlarda pullik obuna (podpiska) doirasida ishga tushiriladi!**\n\n"
        "Barcha talabalar uchun maxsus arzon tariflar tayyorlanmoqda. Bizni kuzatib boring! 💎"
    )
    await message.answer(promo_text, parse_mode="Markdown")

@dp.message()
async def general_text_handler(message: Message):
    # Agar foydalanuvchi buyruq emas, oddiy matn yozsa, Gemini ishga tushadi
    kutilish_xabari = await message.answer("💬 Tahlil qilinmoqda...")
    
    # Kundalik savollarni Gemini'ga yuboramiz
    gemini_javobi = await ask_gemini(message.text)
    
    await kutilish_xabari.delete()
    await message.answer(gemini_javobi, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
