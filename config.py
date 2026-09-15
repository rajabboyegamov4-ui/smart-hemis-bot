import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylining aniq joylashuvini ko'rsatamiz (lokal ishlash uchun):
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Kalitlarni xavfsiz tarzda server muhitidan (environment) olamiz
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HEMIS_BASE_URL = os.getenv("HEMIS_BASE_URL", "https://student.iiau.uz/rest/v1").rstrip("/")
HEMIS_LOGIN = os.getenv("HEMIS_LOGIN")
HEMIS_PASSWORD = os.getenv("HEMIS_PASSWORD")
