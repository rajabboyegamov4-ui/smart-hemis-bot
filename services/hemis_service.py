import aiohttp
from config import HEMIS_BASE_URL

async def get_hemis_token(login, password):
    url = f"{HEMIS_BASE_URL}/auth/login"
    data = {"login": login, "password": password}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    res = await response.json()
                    return res.get('data', {}).get('token')
    except Exception:
        return None
    return None

async def get_hemis_profile(login, password):
    token = await get_hemis_token(login, password)
    if not token:
        return "❌ HEMIS ga ulanishda xatolik! Login yoki parol noto'g'ri."
    
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
        return f"❌ Server xatosi: {str(e)}"
