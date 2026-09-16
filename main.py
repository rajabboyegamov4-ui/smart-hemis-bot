import os
from typing import Optional
from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Yangi tizimga mos importlar
from services.hemis_service import get_hemis_profile, get_hemis_schedule
from services.gemini_service import ask_gemini
from database import get_user, init_db

app = FastAPI(title="Talaba Smart Portali")

# Statik fayllarni ulash (Fayl topilmasa xato bermasligi uchun tekshiruv)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    init_db()

@app.get("/")
async def read_root():
    """Static ichidagi index.html faylini to'g'ridan-to'g'ri ochish."""
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return FileResponse(os.path.join("templates", "index.html"))

# API: Dars jadvali
@app.get("/api/schedule")
async def api_schedule(user_id: Optional[int] = Query(None)):
    if not user_id:
        return JSONResponse({"error": "user_id kiritilmagan"}, status_code=400)
    
    user = get_user(user_id)
    if not user:
        return JSONResponse({"error": "Foydalanuvchi topilmadi. Botdan ro'yxatdan o'ting."}, status_code=404)

    login, password = user
    # Login va parol to'g'ri yuborilyapti
    data = await get_hemis_schedule(login, password)
    return JSONResponse({"schedule": data})

# API: Profil ma'lumotlari
@app.get("/api/profile")
async def api_profile(user_id: Optional[int] = Query(None)):
    if not user_id:
        return JSONResponse({"error": "user_id kiritilmagan"}, status_code=400)
    
    user = get_user(user_id)
    if not user:
        return JSONResponse({"error": "Foydalanuvchi topilmadi. Botdan ro'yxatdan o'ting."}, status_code=404)

    login, password = user
    data = await get_hemis_profile(login, password)
    return JSONResponse({"profile": data})

# API: Gemini AI bilan chat
class ChatRequest(BaseModel):
    prompt: str
    user_id: Optional[int] = None

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    full_prompt = req.prompt
    
    if req.user_id:
        user = get_user(req.user_id)
        if user:
            login, password = user
            profile = await get_hemis_profile(login, password)
            schedule = await get_hemis_schedule(login, password)
            
            full_prompt = f"Foydalanuvchi ma'lumotlari:\n{profile}\n\nJadval:\n{schedule}\n\nFoydalanuvchi savoli: {req.prompt}"

    reply = await ask_gemini(full_prompt)
    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
