import os
from typing import Optional
from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# from services.hemis_service import hemis_client
from services.gemini_service import ask_gemini
from database import get_user, init_db

app = FastAPI(title="Talaba Smart Portali")

# Statik fayllarni ulash
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/")
async def read_root():
    """Static ichidagi index.html faylini to'g'ridan-to'g'ri ochish."""
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    # Agar templates papkasida bo'lsa
    return FileResponse(os.path.join("templates", "index.html"))

# API: Dars jadvali
@app.get("/api/schedule")
async def api_schedule(user_id: Optional[int] = Query(None)):
    if not user_id:
        return JSONResponse({"error": "user_id kiritilmagan"}, status_code=400)
    
    user = await get_user(user_id)
    if not user or not user["hemis_token"]:
        return JSONResponse({"error": "Foydalanuvchi topilmadi"}, status_code=404)

    data = await hemis_client.get_schedule(user["hemis_token"])
    return JSONResponse(data or [])

# API: Profil ma'lumotlari
@app.get("/api/profile")
async def api_profile(user_id: Optional[int] = Query(None)):
    if not user_id:
        return JSONResponse({"error": "user_id kiritilmagan"}, status_code=400)
    
    user = await get_user(user_id)
    if not user or not user["hemis_token"]:
        return JSONResponse({"error": "Foydalanuvchi topilmadi"}, status_code=404)

    data = await hemis_client.get_profile(user["hemis_token"])
    return JSONResponse(data or {})

# API: Gemini AI bilan chat
class ChatRequest(BaseModel):
    prompt: str
    user_id: Optional[int] = None

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    context = ""
    if req.user_id:
        user = await get_user(req.user_id)
        if user and user["hemis_token"]:
            profile = await hemis_client.get_profile(user["hemis_token"])
            schedule = await hemis_client.get_schedule(user["hemis_token"])
            context = f"Talaba: {profile}\nDars jadvali: {schedule}"

    reply = await ask_gemini(req.prompt, context=context)
    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
