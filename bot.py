import asyncio
import io
import os
import google.generativeai as genai
from PyPDF2 import PdfReader
from pptx import Presentation
from pptx.util import Pt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove,
    WebAppInfo,
    FSInputFile
)

from config import BOT_TOKEN, GEMINI_API_KEY
from services.hemis_service import hemis_client
from database import init_db, get_user, save_user, update_language, get_all_users

# Gemini AIni sozlash
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel("gemini-1.5-flash-latest")

WEBAPP_URL = "https://smart-hemis-bot.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

class LoginState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

def get_portal_keyboard(user_id: int):
    url = f"{WEBAPP_URL}?user_id={user_id}"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Talaba Portalini ochish", web_app=WebAppInfo(url=url))],
            [KeyboardButton(text="👤 Profil"), KeyboardButton(text="📅 Dars jadvali")],
            [KeyboardButton(text="🌐 Tilni o'zgartirish"), KeyboardButton(text="📊 Baholar va Davomat")]
        ],
        resize_keyboard=True
    )

# --- AVTOMATIK JADVAL VA MONITORING (FONDA) ---
async def send_daily_reminders():
    users = await get_all_users()
    for telegram_id, token in users:
        try:
            # Bu yerda HEMIS API dan ertangi jadval olinadi. (Hozircha stub qoldiramiz, keyin real API ulaymiz)
            await bot.send_message(
                telegram_id, 
                "🔔 **Ertangi kun uchun dars jadvalingiz:**\n\n1. Oliy matematika (08:30)\n2. Dasturlash (10:00)\n\n_Vaqtida borishni unutmang!_", 
                parse_mode="Markdown"
            )
        except Exception as e:
            pass

# --- TIL TANLASH ---
@dp.message(F.text == "🌐 Tilni o'zgartirish")
@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")]],
        resize_keyboard=True
    )
    await message.answer("O'zingizga qulay tilni tanlang / Выберите язык / Choose language:", reply_markup=markup)

@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"]))
async def process_language(message: types.Message):
    lang_map = {"🇺🇿 O'zbekcha": "uz", "🇷🇺 Русский": "ru", "🇬🇧 English": "en"}
    await update_language(message.from_user.id, lang_map[message.text])
    await message.answer("✅ Til muvaffaqiyatli o'zgartirildi!", reply_markup=get_portal_keyboard(message.from_user.id))

# --- PDF TAHLILI (NotebookLM) ---
@dp.message(F.document)
async def handle_pdf(message: types.Message):
    if not message.document.file_name.endswith('.pdf'):
        return await message.answer("Iltimos, faqat PDF formatidagi fayllarni yuboring.")
    
    msg = await message.answer("⏳ PDF fayl o'qilmoqda va AI tomonidan tahlil qilinmoqda...")
    
    try:
        file = await bot.get_file(message.document.file_id)
        downloaded_file = await bot.download_file(file.file_path)
        
        pdf_reader = PdfReader(downloaded_file)
        text = ""
        for page in pdf_reader.pages[:10]: # Xotira to'lmasligi uchun dastlabki 10 betni o'qiydi
            text += page.extract_text() + "\n"

        prompt = f"Quyidagi PDF kitob/konspekt matnining qisqacha xulosasini va eng asosiy joylarini ajratib ber. Javobni chiroyli qilib, lekin hec qanday yulduzchalar (**) ishlatmasdan yoz:\n\n{text[:3000]}"
        response = ai_model.generate_content(prompt)
        
        await msg.edit_text(f"📑 **PDF Xulosasi:**\n\n{response.text.replace('**', '')}", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text("❌ PDFni o'qishda xatolik yuz berdi. Matn skanerlanmagan rasmli PDF bo'lishi mumkin.")


# --- PREZENTATSIYA (PPTX) YASASH ---
@dp.message(Command("ppt"))
async def create_presentation(message: types.Message):
    topic = message.text.replace('/ppt', '').strip()
    if not topic:
        return await message.answer("Iltimos, mavzuni yozing. Masalan: `/ppt Sun'iy intellekt tarixi`")
    
    msg = await message.answer("🪄 AI prezentatsiya tuzilmasini yaratmoqda. Kuting...")
    
    try:
        # Promptni aniqroq qildik, to'g'ridan-to'g'ri slayd matnini so'raymiz
        prompt = (
            f"'{topic}' mavzusida 4 ta slayd uchun tayyor prezentatsiya matni tuzib ber. "
            "Faqat slaydlar matnini yoz, ortiqcha kirish gaplarsiz. "
            "Har bir slaydni aniq '---SLIDE---' degan so'z bilan boshlang.\n"
            "Ichida 'Sarlavha:' va 'Matn:' so'zlari bo'lsin."
        )
        
        # AI dan javob olish
        response = await ai_model.generate_content_async(prompt)
        
        # AI qo'shib yuborishi mumkin bo'lgan keraksiz belgilarni tozalaymiz
        text = response.text.replace('```text', '').replace('```', '')
        slides_data = text.split("---SLIDE---")
        
        prs = Presentation()
        slide_added = False
        
        for slide_data in slides_data:
            if not slide_data.strip():
                continue
                
            lines = [line.strip() for line in slide_data.strip().split('\n') if line.strip()]
            if not lines:
                continue
                
            title = "Mavzu"
            content_lines = []
            
            for line in lines:
                if line.startswith("Sarlavha:"):
                    title = line.replace("Sarlavha:", "").replace('**', '').strip()
                elif line.startswith("Matn:"):
                    content_lines.append(line.replace("Matn:", "").replace('**', '').strip())
                else:
                    content_lines.append(line.replace('**', '').strip())
            
            content = '\n'.join(content_lines)
            
            slide_layout = prs.slide_layouts[1] 
            slide = prs.slides.add_slide(slide_layout)
            slide.shapes.title.text = title
            slide.placeholders[1].text = content
            slide_added = True
            
        if not slide_added:
            raise ValueError("AI slayd matnini to'g'ri formatda bermadi.")
        
        # Faylni Render serverida xavfsiz papkaga saqlash
        file_path = f"/tmp/{message.from_user.id}_prezentatsiya.pptx"
        if os.name == 'nt': # Agar o'zingizning kompyuteringizda ishlatsangiz
            file_path = f"{message.from_user.id}_prezentatsiya.pptx"
            
        prs.save(file_path)
        
        doc = FSInputFile(file_path, filename=f"{topic}.pptx")
        await bot.send_document(message.chat.id, doc, caption=f"🎉 <b>{topic}</b> mavzusidagi tayyor prezentatsiya!", parse_mode="HTML")
        await msg.delete()
        
        # Yuborib bo'lingach, serverdan tozalab tashlash
        if os.path.exists(file_path):
            os.remove(file_path) 
            
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik yuz berdi. Sabab: {str(e)}")

# --- START VA LOGIN ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)

    # Foydalanuvchi va uning tokeni borligini xavfsiz tekshiramiz
    if user and user.get("hemis_token"):
        name = user.get("full_name") or message.from_user.first_name
        await message.answer(
            f"Assalomu alaykum, {name}!\n\nPortalga xush kelibsiz.",
            reply_markup=get_portal_keyboard(message.from_user.id)
        )
    else:
        await message.answer(
            "👋 Assalomu alaykum!\n\nTalaba portalidan foydalanish uchun HEMIS **Talaba ID (Login)**ingizni kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )
        # MANA SHU QATOR ELSE NING ICHIDA BO'LISHI SHART:
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
    
    try:
        await message.delete()
    except Exception:
        pass

    checking_msg = await message.answer("⏳ HEMIS tizimi tekshirilmoqda...")
    auth_result = await hemis_client.login(login_id, password)
    
    if auth_result and auth_result.get("token"):
        token = auth_result["token"]
        full_name = auth_result.get("profile", {}).get("full_name", message.from_user.full_name)
        
        await save_user(message.from_user.id, token, login_id, full_name, "uz")
        await checking_msg.edit_text(f"✅ Muvaffaqiyatli ulandingiz, {full_name}!")
        await message.answer("👇 Portaldan foydalaning:", reply_markup=get_portal_keyboard(message.from_user.id))
        await state.clear()
    else:
        await checking_msg.edit_text("❌ Login yoki parol noto'g'ri. Qaytadan /start bosib kiring.")
        await state.clear()

async def main():
    await init_db()
    
    # Eslatmalarni har kuni soat 20:00 da ishga tushirish (Toshkent vaqti)
    scheduler.add_job(send_daily_reminders, 'cron', hour=20, minute=0)
    scheduler.start()
    
    print("AI Integratsiyalashgan HEMIS bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
