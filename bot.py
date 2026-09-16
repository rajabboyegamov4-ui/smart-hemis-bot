import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Bizning fayllar
from config import BOT_TOKEN 
from services.gemini_service import ask_gemini
from services.hemis_service import get_hemis_profile, get_hemis_schedule
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

# --- TUGMALAR (Web App to'g'ridan-to'g'ri menyu tugmasiga ulangan) ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Talaba Portalini ochish", web_app=WebAppInfo(url="https://smart-hemis-bot.onrender.com"))],
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
    
    # Foydalanuvchi yuborgan login xabarini chatdan o'chiramiz
    try:
        await message.delete()
    except Exception:
        pass

    if not login_text.isdigit():
        msg = await message.answer("⚠️ Login faqat raqamlardan iborat bo'lishi kerak (Talaba ID raqami). Qaytadan kiriting:")
        await state.update_data(prompt_msg_id=msg.message_id)
        return
        
    await state.update_data(login=login_text)
    
    # Parol so'ralgan xabarni yuboramiz va ID sini saqlaymiz
    msg = await message.answer("Yaxshi! Endi HEMIS parolingizni yuboring:")
    await state.update_data(prompt_msg_id=msg.message_id)
    await state.set_state(RegisterState.waiting_for_password)

@dp.message(RegisterState.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    login = data['login']
    prompt_msg_id = data.get('prompt_msg_id')
    
    # 1. Foydalanuvchi yuborgan parolni darhol o'chiramiz
    try:
        await message.delete()
    except Exception:
        pass
        
    # 2. Botning so'rov xabarini ham o'chiramiz
    if prompt_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass
    
    # Bazaga xavfsiz saqlaymiz
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

@dp.message(F.text == "📅 Dars jadvali")
async def schedule_handler(message: Message):
    user_data = get_user(message.from_user.id)
    if not user_data:
        await message.answer("Siz ro'yxatdan o'tmagansiz. Iltimos /start ni bosing.")
        return
    
    login, password = user_data
    kutilish = await message.answer("🔄 Dars jadvali HEMIS tizimidan yuklanmoqda...")
    
    jadval_matni = await get_hemis_schedule(login, password)
    
    await kutilish.delete()
    await message.answer(jadval_matni, parse_mode="Markdown")

@dp.message(F.text.in_(["📊 Baholar va Davomat", "🌐 Tilni o'zgartirish"]))
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
