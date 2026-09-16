import aiohttp
from config import HEMIS_BASE_URL, HEMIS_LOGIN, HEMIS_PASSWORD

async def get_hemis_token():
    """HEMIS tizimidan avtorizatsiya tokenini olish"""
    url = f"{HEMIS_BASE_URL}/auth/login"
    data = {"login": HEMIS_LOGIN, "password": HEMIS_PASSWORD}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    res = await response.json()
                    return res.get('data', {}).get('token')
    except Exception:
        return None
    return None

async def get_hemis_profile():
    """Talaba profilini tortib kelish"""
    token = await get_hemis_token()
    if not token:
        return "❌ HEMIS ga ulanishda xatolik! Login yoki parol noto'g'ri yoxud HEMIS serveri vaqtinchalik ishlamayapti."
    
    url = f"{HEMIS_BASE_URL}/account/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
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
                return "❌ Profil ma'lumotlarini olishda xatolik yuz berdi."
    except Exception as e:
        return f"❌ Server ulanishida xatolik: {str(e)}"

# Hozircha jadvallar va baholar uchun ham shablon tayyorlab qo'yamiz
async def get_hemis_schedule():
    return "📅 Dars jadvali tizimi hozircha ulanmoqda... (Keyingi yangilanishda tayyor bo'ladi)"

async def get_hemis_grades():
    return "📊 Baholar va davomat tizimi hozircha ulanmoqda... (Keyingi yangilanishda tayyor bo'ladi)"
