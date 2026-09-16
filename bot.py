import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Bizning fayllar
from config import BOT_TOKEN 
from services.gemini_service import ask_gemini
from services.hemis_service import get_hemis_profile, get_hemis_schedule, get_hemis_grades_and_attendance
from database import init_db, save_user, get_user, update_user_language, get_user_language

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bazani ishga tushiramiz
init_db()

# --- 4 TILDAGI TARJIMALAR LUG'ATI ---
LANG_TEXTS = {
    'uz': {
        'welcome': "Xush kelibsiz! Bot xizmatingizga tayyor.",
        'start_reg': "👋 Assalomu alaykum! Talabalar botiga xush kelibsiz.\n\nTizimdan foydalanish uchun HEMIS loginingizni (talaba ID raqamini) yuboring:",
        'login_err': "⚠️ Login faqat raqamlardan iborat bo'lishi kerak (Talaba ID raqami). Qaytadan kiriting:",
        'ask_pass': "Yaxshi! Endi HEMIS parolingizni yuboring:",
        'reg_success': "✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\n\nEndi botdan to'liq foydalanishingiz mumkin.",
        'not_reg': "Siz ro'yxatdan o'tmagansiz. Iltimos /start ni bosing.",
        'wait_profile': "🔄 HEMIS tizimiga ulanmoqda...",
        'wait_schedule': "🔄 Dars jadvali HEMIS tizimidan yuklanmoqda...",
        'wait_grades': "🔄 Baholar va o'zlashtirish yuklanmoqda...",
        'choose_lang': "🌐 O'zingizga qulay tilni tanlang:",
        'lang_changed': "✅ Til muvaffaqiyatli o'zgartirildi: O'zbek tili 🇺🇿",
        'menu_portal': "🚀 Talaba Portalini ochish",
        'menu_profile': "👤 Profil",
        'menu_schedule': "📅 Dars jadvali",
        'menu_lang': "🌐 Tilni o'zgartirish",
        'menu_grades': "📊 Baholar va Davomat",
        'soon': "Bu bo'lim tez kunda ishga tushadi! 🛠"
    },
    'ru': {
        'welcome': "Добро пожаловать! Бот готов к работе.",
        'start_reg': "👋 Здравствуйте! Добро пожаловать в студенческий бот.\n\nДля использования системы отправьте свой логин HEMIS (студенческий ID):",
        'login_err': "⚠️ Логин должен состоять только из цифр (ID студента). Введите снова:",
        'ask_pass': "Отлично! Теперь введите ваш пароль HEMIS:",
        'reg_success': "✅ Вы успешно зарегистрировались!\n\nТеперь вы можете полноценно пользоваться ботом.",
        'not_reg': "Вы не зарегистрированы. Пожалуйста, отправьте /start.",
        'wait_profile': "🔄 Подключение к системе HEMIS...",
        'wait_schedule': "🔄 Загрузка расписания из HEMIS...",
        'wait_grades': "🔄 Загрузка оценок и успеваемости...",
        'choose_lang': "🌐 Выберите удобный язык:",
        'lang_changed': "✅ Язык успешно изменен: Русский 🇷🇺",
        'menu_portal': "🚀 Открыть портал",
        'menu_profile': "👤 Профиль",
        'menu_schedule': "📅 Расписание",
        'menu_lang': "🌐 Изменить язык",
        'menu_grades': "📊 Оценки и посещаемость",
        'soon': "Этот раздел скоро будет запущен! 🛠"
    },
    'en': {
        'welcome': "Welcome! Bot is ready.",
        'start_reg': "👋 Hello! Welcome to the student bot.\n\nPlease send your HEMIS login (student ID) to use the system:",
        'login_err': "⚠️ Login must contain only numbers (Student ID). Enter again:",
        'ask_pass': "Great! Now enter your HEMIS password:",
        'reg_success': "✅ Successfully registered!\n\nYou can now fully use the bot.",
        'not_reg': "You are not registered. Please press /start.",
        'wait_profile': "🔄 Connecting to HEMIS system...",
        'wait_schedule': "🔄 Loading schedule from HEMIS...",
        'wait_grades': "🔄 Loading grades and attendance...",
        'choose_lang': "🌐 Choose your preferred language:",
        'lang_changed': "✅ Language successfully changed: English 🇬🇧",
        'menu_portal': "🚀 Open Student Portal",
        'menu_profile': "👤 Profile",
        'menu_schedule': "📅 Schedule",
        'menu_lang': "🌐 Change Language",
        'menu_grades': "📊 Grades & Attendance",
        'soon': "This section is coming soon! 🛠"
    },
    'tr': {
        'welcome': "Hoş geldiniz! Bot hizmetinize hazırdır.",
        'start_reg': "👋 Merhaba! Öğrenci botuna hoş geldiniz.\n\nSistemi kullanmak için HEMIS giriş bilgilerinizi (öğrenci ID) gönderin:",
        'login_err': "⚠️ Giriş yalnızca rakamlardan oluşmalıdır (Öğrenci ID). Tekrar girin:",
        'ask_pass': "Güzel! Şimdi HEMIS şifrenizi girin:",
        'reg_success': "✅ Başarıyla kayıt oldunuz!\n\nArtık botu tamamen kullanabilirsiniz.",
        'not_reg': "Kayıtlı değilsiniz. Lütfen /start tuşuna basın.",
        'wait_profile': "🔄 HEMIS sistemine bağlanılıyor...",
        'wait_schedule': "🔄 HEMIS'ten ders programı yükleniyor...",
        'wait_grades': "🔄 Notlar ve devam durumu yükleniyor...",
        'choose_lang': "🌐 Size uygun dili seçin:",
        'lang_changed': "✅ Dil başarıyla değiştirildi: Türkçe 🇹🇷",
        'menu_portal': "🚀 Öğrenci Portalını Aç",
        'menu_profile': "👤 Profil",
        'menu_schedule': "📅 Ders Programı",
        'menu_lang': "🌐 Dili Değiştir",
        'menu_grades': "📊 Notlar ve Devamsızlık",
        'soon': "Bu bölüm yakında açılacaktır! 🛠"
    }
}

def get_kb(lang='uz'):
    t = LANG_TEXTS.get(lang, LANG_TEXTS['uz'])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['menu_portal'], web_app=WebAppInfo(url="https://smart-hemis-bot.onrender.com"))],
            [KeyboardButton(text=t['menu_profile']), KeyboardButton(text=t['menu_schedule'])],
            [KeyboardButton(text=t['menu_lang']), KeyboardButton(text=t['menu_grades'])]
        ],
        resize_keyboard=True
    )

# --- HOLATLAR MASHINASI (FSM) ---
class RegisterState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

# --- START VA REGISTRATSIYA ---
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_data = get_user(user_id)
    lang = get_user_language(user_id)
    t = LANG_TEXTS[lang]
    
    # Agar foydalanuvchi bazada mavjud bo'lsa, qaytadan ro'yxatdan o'tkazmaymiz
    if user_data:
        await message.answer(t['welcome'], reply_markup=get_kb(lang))
    else:
        await message.answer(t['start_reg'], reply_markup=ReplyKeyboardRemove())
        await state.set_state(RegisterState.waiting_for_login)

@dp.message(RegisterState.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    t = LANG_TEXTS[lang]
    login_text = message.text.strip()
    
    try:
        await message.delete()
    except Exception:
        pass

    if not login_text.isdigit():
        msg = await message.answer(t['login_err'])
        await state.update_data(prompt_msg_id=msg.message_id)
        return
        
    await state.update_data(login=login_text)
    
    msg = await message.answer(t['ask_pass'])
    await state.update_data(prompt_msg_id=msg.message_id)
    await state.set_state(RegisterState.waiting_for_password)

@dp.message(RegisterState.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    t = LANG_TEXTS[lang]
    password = message.text.strip()
    data = await state.get_data()
    login = data['login']
    prompt_msg_id = data.get('prompt_msg_id')
    
    try:
        await message.delete()
    except Exception:
        pass
        
    if prompt_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prompt_msg_id)
        except Exception:
            pass
    
    save_user(user_id, login, password)
    await state.clear()
    
    await message.answer(t['reg_success'], reply_markup=get_kb(lang))

# --- TILNI O'ZGARTIRISH ---
@dp.message(F.text.in_(["🌐 Tilni o'zgartirish", "🌐 Изменить язык", "🌐 Change Language", "🌐 Dili Değiştir"]))
async def lang_menu_handler(message: Message):
    lang = get_user_language(message.from_user.id)
    t = LANG_TEXTS[lang]
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="O'zbekcha 🇺🇿", callback_data="lang_uz"),
             InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en"),
             InlineKeyboardButton(text="Türkçe 🇹🇷", callback_data="lang_tr")]
        ]
    )
    await message.answer(t['choose_lang'], reply_markup=keyboard)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    new_lang = callback.data.split("_")[1]
    update_user_language(user_id, new_lang)
    
    t = LANG_TEXTS[new_lang]
    await callback.message.delete()
    await callback.message.answer(t['lang_changed'], reply_markup=get_kb(new_lang))
    await callback.answer()

# --- HEMIS TUGMALARI ---
@dp.message(F.text.in_(["👤 Profil", "👤 Профиль", "👤 Profile"]))
async def profil_handler(message: Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    lang = get_user_language(user_id)
    t = LANG_TEXTS[lang]
    
    if not user_data:
        await message.answer(t['not_reg'])
        return
    
    login, password = user_data
    kutilish = await message.answer(t['wait_profile'])
    
    profil_malumoti = await get_hemis_profile(login, password)
    
    await kutilish.delete()
    await message.answer(profil_malumoti, parse_mode="Markdown")

@dp.message(F.text.in_(["📅 Dars jadvali", "📅 Расписание", "📅 Schedule", "📅 Ders Programı"]))
async def schedule_handler(message: Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    lang = get_user_language(user_id)
    t = LANG_TEXTS[lang]
    
    if not user_data:
        await message.answer(t['not_reg'])
        return
    
    login, password = user_data
    kutilish = await message.answer(t['wait_schedule'])
    
    jadval_matni = await get_hemis_schedule(login, password)
    
    await kutilish.delete()
    await message.answer(jadval_matni, parse_mode="Markdown")

@dp.message(F.text.in_(["📊 Baholar va Davomat", "📊 Оценки и посещаемость", "📊 Grades & Attendance", "📊 Notlar ve Devamsızlık"]))
async def grades_handler(message: Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    lang = get_user_language(user_id)
    t = LANG_TEXTS[lang]
    
    if not user_data:
        await message.answer(t['not_reg'])
        return
    
    login, password = user_data
    kutilish = await message.answer(t['wait_grades'])
    
    grades_matni = await get_hemis_grades_and_attendance(login, password)
    
    await kutilish.delete()
    await message.answer(grades_matni, parse_mode="Markdown")

# --- GEMINI (AI) VA TEST ---
@dp.message(Command("ppt"))
async def ppt_handler(message: Message):
    await message.answer("🚀 **Taqdimot tayyorlash (PPT)** tez kunda pullik obunada ishga tushadi!", parse_mode="Markdown")

@dp.message(Command("test"))
async def test_handler(message: Message):
    user_text = message.text.replace("/test", "").strip()
    if not user_text:
        await message.answer("⚠️ Iltimos, test mavzusini yozing. Masalan:\n`/test O'zbekiston tarixi 10 ta savol`", parse_mode="Markdown")
        return

    kutilish = await message.answer("✍️ Testlar tuzilmoqda, biroz kuting...")
    try:
        prompt = f"Quyidagi mavzu bo'yicha sifatli test tuzib ber. Variantlari bilan bo'lsin va oxirida javoblarini ham ko'rsat:\n\n{user_text}"
        javob = await ask_gemini(prompt)
        await kutilish.delete()
        await message.answer(javob, parse_mode="Markdown")
    except Exception as e:
        await kutilish.delete()
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

@dp.message()
async def general_text_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return

    # Barcha tillardagi menyu tugmalari ro'yxati (Bularga Gemini javob bermasligi kerak)
    menu_texts = [
        "🌐 Tilni o'zgartirish", "🌐 Изменить язык", "🌐 Change Language", "🌐 Dili Değiştir",
        "👤 Profil", "👤 Профиль", "👤 Profile",
        "📅 Dars jadvali", "📅 Расписание", "📅 Schedule", "📅 Ders Programı",
        "📊 Baholar va Davomat", "📊 Оценки и посещаемость", "📊 Grades & Attendance", "📊 Notlar ve Devamsızlık",
        "🚀 Talaba Portalini ochish", "🚀 Открыть портал", "🚀 Open Student Portal", "🚀 Öğrenci Portalını Aç"
    ]
    if message.text in menu_texts:
        return

    # Foydalanuvchi ro'yxatdan o'tganligini tekshiramiz
    user_data = get_user(message.from_user.id)
    if not user_data:
        await message.answer("Siz ro'yxatdan o'tmagansiz. Iltimos /start ni bosing.")
        return

    kutilish_xabari = await message.answer("💬 Tahlil qilinmoqda...")
    try:
        gemini_javobi = await ask_gemini(message.text)
        await kutilish_xabari.delete()
        await message.answer(gemini_javobi, parse_mode="Markdown")
    except Exception as e:
        await kutilish_xabari.delete()
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
