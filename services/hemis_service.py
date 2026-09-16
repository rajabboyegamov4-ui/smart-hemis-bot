import aiohttp
from config import HEMIS_BASE_URL

async def get_hemis_token(login, password):
    url = f"{HEMIS_BASE_URL}/auth/login"
    data = {"login": login, "password": password}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, timeout=10) as response:
                if response.status == 200:
                    res = await response.json()
                    return res.get('data', {}).get('token')
    except Exception:
        return None
    return None

async def get_hemis_profile(login, password):
    token = await get_hemis_token(login, password)
    if not token:
        return "❌ HEMIS bilan xatolik! Login yoki parol noto'g'ri yoki server ishlamayapti."
    
    url = f"{HEMIS_BASE_URL}/account/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    res = await response.json()
                    data = res.get('data', {})
                    ism = data.get('full_name', 'Noma\'lum')
                    fakultet = data.get('faculty', {}).get('name', 'Noma\'lum')
                    guruh = data.get('group', {}).get('name', 'Noma\'lum')
                    kurs = data.get('level', {}).get('name', 'Noma\'lum')
                    
                    return (
                        f"👤 **Sizning Profilingiz:**\n\n"
                        f"🎓 **F.I.Sh:** {ism}\n"
                        f"🏢 **Fakultet:** {fakultet}\n"
                        f"📈 **Kurs:** {kurs}\n"
                        f"👥 **Guruh:** {guruh}"
                    )
                return "❌ Profil ma'lumotlarini o'qishda xatolik yuz berdi."
    except Exception as e:
        return f"❌ Server xatosi: {str(e)}"

async def get_hemis_schedule(login, password):
    token = await get_hemis_token(login, password)
    if not token:
        return "❌ HEMIS bilan xatolik! Login yoki parol noto'g'ri."
    
    url = f"{HEMIS_BASE_URL}/education/schedule"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    res = await response.json()
                    data = res.get('data', [])
                    
                    if not data:
                        return "📅 Hozircha joriy hafta uchun dars jadvali topilmadi."
                    
                    schedule_text = "📅 **Sizning Dars Jadvalingiz:**\n\n"
                    
                    for day in data:
                        kun_nomi = day.get('week_name', 'Kun')
                        sana = day.get('date', '')
                        schedule_text += f"📌 **{kun_nomi} ({sana})**\n"
                        
                        lessons = day.get('pairs', [])
                        if not lessons:
                            schedule_text += "   *Darslar yo'q (Dam olish kuni)*\n\n"
                        else:
                            for lesson in lessons:
                                vaqt = lesson.get('start_time', '')
                                fan = lesson.get('subject', {}).get('name', 'Fan nomi yo\'q')
                                xona = lesson.get('room', {}).get('name', 'Xona ko\'rsatilmagan')
                                oqituvchi = lesson.get('employee', {}).get('name', '')
                                
                                schedule_text += f"  🕒 {vaqt} | **{fan}**\n  📍 Xona: {xona} | 👨‍🏫 {oqituvchi}\n\n"
                        
                        schedule_text += "-------------------\n"
                    
                    return schedule_text
                
                return "❌ Dars jadvalini yuklab bo'lmadi. HEMIS vaqtincha ishlamayotgan bo'lishi mumkin."
    except Exception as e:
        return f"❌ Jadvalni olishda xatolik: {str(e)}"

# --- YAGI QO'SHILGAN: Baholar va Davomat ---
async def get_hemis_grades_and_attendance(login, password):
    token = await get_hemis_token(login, password)
    if not token:
        return "❌ HEMIS bilan xatolik! Login yoki parol noto'g'ri."
    
    # HEMIS o'zlashtirish (performance) endpointi
    url = f"{HEMIS_BASE_URL}/education/performance"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    res = await response.json()
                    data = res.get('data', [])
                    
                    if not data:
                        return "📊 Hozircha baholar va o'zlashtirish ma'lumotlari topilmadi."
                    
                    text = "📊 **Sizning O'zlashtirish va Baholaringiz:**\n\n"
                    for item in data:
                        fan = item.get('subject', {}).get('name', 'Fan nomi')
                        umumiy = item.get('total_grade', 'N/A')
                        reyting = item.get('grade_name', 'Baholanmagan')
                        
                        text += f"📚 **{fan}**\n   🔹 Umumiy ball: {umumiy} | Baho: {reyting}\n\n"
                    
                    return text
                else:
                    return "⚠️ Baholar bo'limi hozircha ushbu HEMIS serverida ochiq emas yoki ma'lumot topilmadi."
    except Exception as e:
        return f"❌ Baholarni olishda xatolik: {str(e)}"
