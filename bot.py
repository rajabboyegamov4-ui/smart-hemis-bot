import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Config fayldan tokenni chaqiramiz
from config import BOT_TOKEN 
from services.gemini_service import ask_gemini

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- 1. TUGMALAR (Klaviatura) YARATISH ---
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
    # Start bosilganda matn va tugmalar birga chiqadi
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu)


# --- 3. HEMIS TUGMALARI UCHUN HANDLERLAR ---
# Bu qism bot tugmalarni "AI" emas, aynan tugma deb tushunishi uchun kerak

@dp.message(F.text == "👤 Profil")
async def profil_handler(message: Message):
    # Bu yerga o'zingizning HEMIS profilni tortib keluvchi kodingizni qo'shasiz (hozircha vaqtinchalik javob)
    await message.answer("Sizning profilingiz ma'lumotlari yuklanmoqda... (HEMIS API ga ulanadi)")

@dp.message(F.text == "📅 Dars jadvali")
async def dars_jadvali_handler(message: Message):
    await message.answer("Sizning dars jadvalingiz yuklanmoqda... (HEMIS API ga ulanadi)")

@dp.message(F.text == "📊 Baholar va Davomat")
async def baholar_handler(message: Message):
    await message.answer("Baholar va davomat ma'lumotlari yuklanmoqda... (HEMIS API ga ulanadi)")

@dp.message(F.text == "🌐 Tilni o'zgartirish")
async def til_handler(message: Message):
    await message.answer("Tilni o'zgartirish menyusi:")

@dp.message(F.text == "🚀 Talaba Portalini ochish")
async def portal_handler(message: Message):
    await message.answer("Talaba portaliga ulanish:")


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
# DIQQAT: AI har doim kodning eng oxirida turishi shart! Agar uni tepaga qoysangiz tugmalarni ham tahlil qilib yuboradi.
@dp.message()
async def general_text_handler(message: Message):
    kutilish_xabari = await message.answer("💬 Tahlil qilinmoqda...")
    
    try:
        # Kundalik savollarni Gemini'ga yuboramiz
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
