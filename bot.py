import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN 
from services.gemini_service import ask_gemini
from services.hemis_service import get_hemis_profile
from database import init_db, save_user, get_user

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bazani ishga tushiramiz
init_db()

# --- HOLATLAR MASHINASI (FSM) ---
class RegisterState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

# --- TUGMALAR ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Talaba Portalini ochish")],
        [KeyboardButton(text="👤 Profil"), KeyboardButton(text="📅 Dars jadvali")],
        [KeyboardButton(text="🌐 Tilni o'zgartirish"), KeyboardButton(text="📊 Baholar va Davomat")]
    ],
    resize_keyboard=True
)

# --- START VA REGISTRATSIYA ---
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user_data = get_user(message.from_user.id)
    
    if user_data:
        await message.answer("Xush kelibsiz! Bot xizmatingizga tayyor.", reply_markup=main_menu)
    else:
        await message.answer(
            "👋 Assalomu alaykum! Talabalar botiga xush kelibsiz.\n\n"
            "Tizimdan foydalanish uchun HEMIS loginingizni (talaba ID raqamini) yuboring:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegisterState.waiting_for_login)

@dp.message(RegisterState.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    login_text = message.text.strip()
    if not login_text.isdigit():
        await message.answer("⚠️ Login faqat raqamlardan iborat bo'lishi kerak (Talaba ID raqami). Qaytadan kiriting:")
        return
        
    await state.update_data(login=login_text)
    await message.answer("Yaxshi! Endi HEMIS parolingizni yuboring:")
    await state.set_state(RegisterState.waiting_for_password)

@dp.message(RegisterState.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    login = data['login']
    
    # Bazaga saqlaymiz
    save_user(message.from_user.id, login, password)
    await state.clear()
    
    await message.answer("✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\n\nEndi botdan to'liq foydalanishingiz mumkin.", reply_markup=main_menu)

# --- HEMIS TUGMALARI ---
@dp.message(F.text == "👤 Profil")
async def profil_handler(message: Message):
    user_data = get_user(message.from_user.id)
    if not user_data:
        await message.answer("Siz ro'yxatdan o'tmagansiz. Iltimos /start ni bosing.")
        return
    
    login, password = user_data
    kutilish = await message.answer("🔄 HEMIS tizimiga ulanmoqda...")
    
    profil_malumoti = await get_hemis_profile(login, password)
    
    await kutilish.delete()
    await message.answer(profil_malumoti, parse_mode="Markdown")

@dp.message(F.text == "🚀 Talaba Portalini ochish")
async def portal_handler(message: Message):
    # Tugmaning o'zini bosganda to'g'ridan-to'g'ri brauzerni ochuvchi inline tugma chiqadi
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Talaba Portalini ochish", url="https://smart-hemis-bot.onrender.com")]
        ]
    )
    await message.answer(
        "🌐 Pastdagi tugmani bosing:", 
        reply_markup=keyboard
    )

@dp.message(F.text.in_(["📅 Dars jadvali", "📊 Baholar va Davomat", "🌐 Tilni o'zgartirish"]))
async def boshqa_tugmalar(message: Message):
    await message.answer("Bu bo'lim tez kunda ishga tushadi! 🛠")

# --- GEMINI (AI) ---
@dp.message(Command("ppt"))
async def ppt_handler(message: Message):
    await message.answer("🚀 **Taqdimot tayyorlash (PPT)** tez kunda pullik obunada ishga tushadi!", parse_mode="Markdown")

@dp.message()
async def general_text_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return

    kutilish_xabari = await message.answer("💬 Tahlil qilinmoqda...")
    try:
        gemini_javobi = await ask_gemini(message.text)
        await kutilish_xabari.delete()
        await message.answer(gemini_javobi, parse_mode="Markdown")
    except Exception as e:
        await kutilish_xabari.delete()
        await message.answer(f"Xatolik yuz berdi: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
