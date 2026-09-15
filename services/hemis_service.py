import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
from typing import Optional, Dict, Any
from config import HEMIS_BASE_URL

class HemisClient:
    def __init__(self, base_url: str = HEMIS_BASE_URL):
        self.base_url = base_url.rstrip("/")

    async def login(self, login_id: str, password: str) -> Optional[Dict[str, Any]]:
        """Talaba login va paroli orqali token hamda profil ma'lumotlarini olish."""
        url = f"{self.base_url}/auth/login"
        payload = {
            "login": login_id,
            "password": password
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        token = data.get("data", {}).get("token") or data.get("token")
                        if token:
                            profile = await self.get_profile(token)
                            return {
                                "token": token,
                                "profile": profile
                            }
                    else:
                        print(f"HEMIS Login rad etildi. Status: {resp.status}")
                        return None
        except Exception as e:
            print(f"HEMIS Login ulanish xatosi: {e}")
            return None

    async def _fetch(self, endpoint: str, token: str) -> Optional[Any]:
        """Berilgan talaba tokeni orqali API so'rov yuborish."""
        if not token:
            return None

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        res_data = await resp.json()
                        return res_data.get("data", res_data)
                    return None
        except Exception as e:
            print(f"HEMIS API xatosi ({endpoint}): {e}")
            return None

    async def get_profile(self, token: str) -> Optional[Dict[str, Any]]:
        return await self._fetch("/account/me", token)

    async def get_schedule(self, token: str) -> Optional[Any]:
        return await self._fetch("/education/schedule", token)

    async def get_performance(self, token: str) -> Optional[Any]:
        return await self._fetch("/education/performance", token)

    async def get_attendance(self, token: str) -> Optional[Any]:
        return await self._fetch("/education/attendance", token)

# Ilova bo'ylab ishlatiladigan yagona mijoz obyekti
hemis_client = HemisClient()