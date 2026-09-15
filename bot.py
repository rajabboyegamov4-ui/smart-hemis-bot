import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove,
    WebAppInfo
)

from config import BOT_TOKEN
from services.hemis_service import hemis_client
from database import init_db, get_user, save_user

WEBAPP_URL = "https://abnormal-density-monsoon.ngrok-free.dev"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Ro'yxatdan o'tish bosqichlari
class LoginState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

def get_portal_keyboard(user_id: int):
    # WebApp URL ga telegram_id qo'shib yuboriladi
    url = f"{WEBAPP_URL}?user_id={user_id}"
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🚀 Talaba Portalini ochish",
                    web_app=WebAppInfo(url=url)
                )
            ]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    
    if user and user["hemis_token"]:
        name = user["full_name"] or message.from_user.first_name
        await message.answer(
            f"Assalomu alaykum, {name}!\n\n"
            "Siz tizimga ulangansiz. Portalni ochish uchun pastdagi tugmani bosing:",
            reply_markup=get_portal_keyboard(message.from_user.id)
        )
    else:
        await message.answer(
            "👋 Assalomu alaykum!\n\n"
            "Talaba portalidan foydalanish uchun HEMIS tizimidagi **Talaba ID (Login)**ingizni kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(LoginState.waiting_for_login)

@dp.message(LoginState.waiting_for_login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(hemis_login=message.text.strip())
    await message.answer("🔑 Endi HEMIS **parolingizni** kiriting:")
    await state.set_state(LoginState.waiting_for_password)

@dp.message(LoginState.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    login_id = data["hemis_login"]
    
    # Parol yozilgan xabarni xavfsizlik uchun darhol o'chirib tashlaymiz
    try:
        await message.delete()
    except Exception:
        pass

    checking_msg = await message.answer("⏳ HEMIS tizimi orqali tekshirilmoqda...")
    
    auth_result = await hemis_client.login(login_id, password)
    
    if auth_result and auth_result.get("token"):
        token = auth_result["token"]
        profile = auth_result.get("profile") or {}
        full_name = profile.get("full_name", message.from_user.full_name)
        
        # Bazaga saqlash
        await save_user(
            telegram_id=message.from_user.id,
            hemis_token=token,
            student_id=login_id,
            full_name=full_name
        )
        
        await checking_msg.edit_text(f"✅ Muvaffaqiyatli ulandingiz, {full_name}!")
        await message.answer(
            "Pastdagi tugma orqali shaxsiy portalingizni ochishingiz mumkin 👇",
            reply_markup=get_portal_keyboard(message.from_user.id)
        )
        await state.clear()
    else:
        await checking_msg.edit_text(
            "❌ Login yoki parol noto'g'ri bo'ldi. Qaytadan /start bosib urinib ko'ring."
        )
        await state.clear()

@dp.message(Command("logout"))
async def cmd_logout(message: types.Message):
    await save_user(message.from_user.id, "", "", "")
    await message.answer("Tizimdan chiqdingiz. Qayta kirish uchun /start bosing.", reply_markup=ReplyKeyboardRemove())

async def main():
    await init_db()
    print("Bot ko'p foydalanuvchili rejimda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())