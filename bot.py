import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Config va Servislarni chaqiramiz
from config import BOT_TOKEN 
from services.gemini_service import ask_gemini
from services.hemis_service import get_hemis_profile, get_hemis_schedule, get_hemis_grades

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- 1. TUGMALAR YARATISH ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Talaba Portalini ochish")],
        [KeyboardButton(text="👤 Profil"), KeyboardButton(text="📅 Dars jadvali")],
        [KeyboardButton(text="🌐 Tilni o'zgartirish"), KeyboardButton(text="📊 Baholar va Davomat")]
    ],
    resize_keyboard=True
)

# --- 2. START BUYRUG'I ---
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
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu)

# --- 3. HEMIS TUGMALARI UCHUN HANDLERLAR ---
@dp.message(F.text == "👤 Profil")
async def profil_handler(message: Message):
    kutilish = await message.answer("🔄 HEMIS tizimiga ulanmoqda...")
    profil_malumoti = await get_hemis_profile()
    await kutilish.delete()
    await message.answer(profil_malumoti, parse_mode="Markdown")

@dp.message(F.text == "📅 Dars jadvali")
async def dars_jadvali_handler(message: Message):
    jadval = await get_hemis_schedule()
    await message.answer(jadval)

@dp.message(F.text == "📊 Baholar va Davomat")
async def baholar_handler(message: Message):
    baholar = await get_hemis_grades()
    await message.answer(baholar)

@dp.message(F.text == "🌐 Tilni o'zgartirish")
async def til_handler(message: Message):
    await message.answer("Tez kunda ko'p tilli funksiya qo'shiladi! 🌍")

@dp.message(F.text == "🚀 Talaba Portalini ochish")
async def portal_handler(message: Message):
    await message.answer("Talaba portaliga ulanish uchun bosing: [HEMIS Portal](https://student.iiau.uz/)", parse_mode="Markdown", disable_web_page_preview=True)

# --- 4. CLAUDE PPT BUYRUG'I (/ppt) ---
@dp.message(Command("ppt"))
async def ppt_handler(message: Message):
    promo_text = (
        "🚀 **Taqdimot tayyorlash (PPT) xizmati haqida:**\n\n"
        "Ushbu funksiya dunyodagi eng kuchli **Claude 3.5 Sonnet** sun'iy intellekti asosida ishlaydi. "
        "Sizga mukammal slaydlar va taqdimot matnlarini yozib beradigan, vaqtingizni 100 barobar tejaydigan bu maxsus rejim "
        "**eng yaqin fursatlarda pullik obuna (podpiska) doirasida ishga tushiriladi!**\n\n"
        "Barcha talabalar uchun maxsus arzon tariflar tayyorlanmoqda. Bizni kuzatib boring! 💎"
    )
    await message.answer(promo_text, parse_mode="Markdown")

# --- 5. QOLGAN BARCHA MATNLAR UCHUN (GEMINI) ---
@dp.message()
async def general_text_handler(message: Message):
    kutilish_xabari = await message.answer("💬 Tahlil qilinmoqda...")
    try:
        gemini_javobi = await ask_gemini(message.text)
        await kutilish_xabari.delete()
        await message.answer(gemini_javobi, parse_mode="Markdown")
    except Exception as e:
        await kutilish_xabari.delete()
        await message.answer(f"Kechirasiz, xatolik yuz berdi: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
