"""
HEMIS Service — qayta yozilgan versiya.

Asosiy o'zgarishlar:
  1. Token keshlanadi (TokenManager) — har so'rovda qayta login qilinmaydi.
  2. 401 kelganda token avtomatik yangilanadi va so'rov 1 marta qayta yuboriladi.
  3. Funksiyalar STRUKTURALI dict qaytaradi (grafik chizish uchun).
  4. Matn formatlash alohida `format_*` funksiyalarida (bot uchun).
  5. Turli HEMIS serverlaridagi har xil JSON strukturalari universal parser bilan o'qiladi.
  6. Bitta aiohttp.ClientSession qayta ishlatiladi (har safar yangisi ochilmaydi).
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Optional

import aiohttp

from config import HEMIS_BASE_URL

# Token necha soniya amal qiladi deb hisoblaymiz (HEMIS odatda ~1 soat beradi).
TOKEN_TTL = 50 * 60
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)


class HemisError(Exception):
    """HEMIS bilan ishlashda yuzaga kelgan xatolik."""

    def __init__(self, message: str, code: str = "unknown"):
        super().__init__(message)
        self.message = message
        self.code = code  # auth | server | network | notfound | unknown


# ---------------------------------------------------------------------------
# Token boshqaruvi
# ---------------------------------------------------------------------------
class TokenManager:
    """Login bo'yicha tokenlarni xotirada saqlaydi va kerak bo'lganda yangilaydi."""

    def __init__(self):
        self._tokens: dict[str, tuple[str, float]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock_for(self, login: str) -> asyncio.Lock:
        if login not in self._locks:
            self._locks[login] = asyncio.Lock()
        return self._locks[login]

    def invalidate(self, login: str) -> None:
        self._tokens.pop(login, None)

    async def get_token(self, session, login: str, password: str, force: bool = False) -> str:
        if not force:
            cached = self._tokens.get(login)
            if cached and cached[1] > time.time():
                return cached[0]

        # Bir vaqtda bir nechta so'rov kelsa, faqat bittasi login qilsin.
        async with self._lock_for(login):
            cached = self._tokens.get(login)
            if not force and cached and cached[1] > time.time():
                return cached[0]

            token = await self._login(session, login, password)
            self._tokens[login] = (token, time.time() + TOKEN_TTL)
            return token

    async def _login(self, session, login: str, password: str) -> str:
        url = f"{HEMIS_BASE_URL}/auth/login"
        try:
            async with session.post(url, data={"login": login, "password": password}) as resp:
                if resp.status in (400, 401, 403):
                    raise HemisError("Login yoki parol noto'g'ri.", code="auth")
                if resp.status != 200:
                    raise HemisError(f"HEMIS serveri javob bermadi ({resp.status}).", code="server")

                payload = await resp.json(content_type=None)
                token = _dig(payload, "data.token") or _dig(payload, "token")
                if not token:
                    raise HemisError("Serverdan token kelmadi.", code="server")
                return token
        except aiohttp.ClientError as exc:
            raise HemisError(f"Tarmoq xatosi: {exc}", code="network") from exc
        except asyncio.TimeoutError as exc:
            raise HemisError("HEMIS serveri javobini kutish vaqti tugadi.", code="network") from exc


_token_manager = TokenManager()
_session: Optional[aiohttp.ClientSession] = None


async def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=REQUEST_TIMEOUT)
    return _session


async def close_session() -> None:
    """FastAPI shutdown / bot to'xtaganda chaqiring."""
    global _session
    if _session and not _session.closed:
        await _session.close()
    _session = None


# ---------------------------------------------------------------------------
# Universal so'rov yuborish (401 bo'lsa tokenni yangilab qayta urinadi)
# ---------------------------------------------------------------------------
async def hemis_request(login: str, password: str, endpoint: str, params: dict | None = None) -> Any:
    session = await get_session()
    url = f"{HEMIS_BASE_URL}{endpoint}"

    for attempt in range(2):
        token = await _token_manager.get_token(session, login, password, force=(attempt == 1))
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 401:
                    _token_manager.invalidate(login)
                    if attempt == 0:
                        continue  # tokenni yangilab qayta urinamiz
                    raise HemisError("Sessiya tugadi, qayta login qiling.", code="auth")
                if resp.status == 404:
                    raise HemisError("Bu bo'lim ushbu HEMIS serverida mavjud emas.", code="notfound")
                if resp.status != 200:
                    raise HemisError(f"HEMIS xatosi ({resp.status}).", code="server")

                payload = await resp.json(content_type=None)
                return payload.get("data", payload) if isinstance(payload, dict) else payload
        except aiohttp.ClientError as exc:
            raise HemisError(f"Tarmoq xatosi: {exc}", code="network") from exc
        except asyncio.TimeoutError as exc:
            raise HemisError("So'rov vaqti tugadi.", code="network") from exc

    raise HemisError("So'rovni bajarib bo'lmadi.", code="unknown")


# ---------------------------------------------------------------------------
# JSON'dan xavfsiz o'qish yordamchilari
# ---------------------------------------------------------------------------
def _dig(data: Any, path: str, default: Any = None) -> Any:
    """'data.token' yoki 'subject.name' kabi yo'l bo'yicha qiymat oladi."""
    current = data
    for key in path.split("."):
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and current and key.isdigit():
            idx = int(key)
            current = current[idx] if idx < len(current) else None
        else:
            return default
        if current is None:
            return default
    return current


def _first(data: Any, *paths: str, default: Any = None) -> Any:
    """Bir nechta variantdan birinchi topilganini qaytaradi (server farqlari uchun)."""
    for path in paths:
        value = _dig(data, path)
        if value not in (None, "", []):
            return value
    return default


def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "data", "results"):
            if isinstance(value.get(key), list):
                return value[key]
        return [value]
    return []


def _name_of(value: Any) -> str:
    """Maydon {'name': ...} dict, oddiy string yoki ro'yxat bo'lishi mumkin."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("name") or value.get("title") or value.get("full_name") or ""
    if isinstance(value, list):
        return ", ".join(filter(None, (_name_of(v) for v in value)))
    return ""


def _to_date(value: Any) -> str:
    """Unix timestamp yoki 'YYYY-MM-DD' ni o'qiladigan sanaga aylantiradi."""
    if not value:
        return ""
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        try:
            return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return str(value)
    return str(value)


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Profil
# ---------------------------------------------------------------------------
async def fetch_profile(login: str, password: str) -> dict:
    data = await hemis_request(login, password, "/account/me")
    return {
        "full_name": _first(data, "full_name", "name", default="Noma'lum"),
        "student_id": _first(data, "student_id_number", "student_id", default=""),
        "faculty": _name_of(_first(data, "faculty", "department")),
        "group": _name_of(data.get("group")),
        "level": _name_of(_first(data, "level", "course")),
        "specialty": _name_of(data.get("specialty")),
        "education_form": _name_of(data.get("educationForm") or data.get("education_form")),
        "semester": _name_of(data.get("semester")),
        "avatar": _first(data, "image", "picture", default=""),
    }


def format_profile(p: dict) -> str:
    lines = [
        "👤 **Sizning Profilingiz:**\n",
        f"🎓 **F.I.Sh:** {p['full_name']}",
        f"🏢 **Fakultet:** {p['faculty'] or '—'}",
        f"📈 **Kurs:** {p['level'] or '—'}",
        f"👥 **Guruh:** {p['group'] or '—'}",
    ]
    if p.get("specialty"):
        lines.append(f"📖 **Yo'nalish:** {p['specialty']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dars jadvali
# ---------------------------------------------------------------------------
WEEKDAYS_UZ = ["Dushanba", "Seshanba", "Chorshanba", "Payshamba", "Juma", "Shanba", "Yakshanba"]


async def fetch_schedule(login: str, password: str, params: dict | None = None) -> list[dict]:
    """Kunlar bo'yicha guruhlangan jadval qaytaradi.

    Turli HEMIS serverlari 2 xil format beradi:
      A) [{week_name, date, pairs: [...]}, ...]  — kunlarga guruhlangan
      B) [{lesson_date, lessonPair: {...}, subject: {...}}, ...] — tekis ro'yxat
    Ikkalasi ham bir xil natijaga keltiriladi.
    """
    raw = _as_list(await hemis_request(login, password, "/education/schedule", params))
    if not raw:
        return []

    # A varianti: ichida 'pairs'/'lessons' bo'lsa — allaqachon guruhlangan
    if any(isinstance(item, dict) and (item.get("pairs") or item.get("lessons")) for item in raw):
        days = []
        for item in raw:
            lessons = _as_list(item.get("pairs") or item.get("lessons"))
            days.append({
                "date": _to_date(_first(item, "date", "lesson_date")),
                "day_name": _first(item, "week_name", "day_name", default=""),
                "lessons": [_parse_lesson(l) for l in lessons],
            })
        return days

    # B varianti: tekis ro'yxatni sana bo'yicha o'zimiz guruhlaymiz
    grouped: dict[str, list[dict]] = {}
    for item in raw:
        date = _to_date(_first(item, "lesson_date", "date"))
        grouped.setdefault(date, []).append(_parse_lesson(item))

    days = []
    for date, lessons in sorted(grouped.items()):
        try:
            day_name = WEEKDAYS_UZ[datetime.strptime(date, "%Y-%m-%d").weekday()]
        except ValueError:
            day_name = ""
        lessons.sort(key=lambda x: x["start_time"])
        days.append({"date": date, "day_name": day_name, "lessons": lessons})
    return days


def _parse_lesson(item: dict) -> dict:
    return {
        "start_time": _first(item, "lessonPair.start_time", "start_time", "lesson_pair.start_time", default=""),
        "end_time": _first(item, "lessonPair.end_time", "end_time", "lesson_pair.end_time", default=""),
        "pair_name": _first(item, "lessonPair.name", "lesson_pair.name", default=""),
        "subject": _name_of(_first(item, "subject", "curriculumSubject")) or "Fan nomi yo'q",
        "room": _name_of(_first(item, "auditorium", "room")) or "",
        "teacher": _name_of(_first(item, "employee", "teacher", "employee_list")) or "",
        "type": _name_of(_first(item, "trainingType", "training_type", "lessonType")) or "",
        "building": _name_of(_first(item, "building", "auditorium.building")) or "",
    }


def format_schedule(days: list[dict]) -> str:
    if not days:
        return "📅 Hozircha joriy hafta uchun dars jadvali topilmadi."

    out = ["📅 **Sizning Dars Jadvalingiz:**\n"]
    for day in days:
        header = " ".join(filter(None, [day["day_name"], f"({day['date']})" if day["date"] else ""]))
        out.append(f"📌 **{header or 'Kun'}**")
        if not day["lessons"]:
            out.append("   _Darslar yo'q_\n")
            continue
        for lesson in day["lessons"]:
            time_part = lesson["start_time"]
            if lesson["end_time"]:
                time_part += f"–{lesson['end_time']}"
            out.append(f"  🕒 {time_part} | **{lesson['subject']}**")
            details = []
            if lesson["room"]:
                details.append(f"📍 {lesson['room']}")
            if lesson["teacher"]:
                details.append(f"👨‍🏫 {lesson['teacher']}")
            if lesson["type"]:
                details.append(f"🏷 {lesson['type']}")
            if details:
                out.append("  " + " | ".join(details))
            out.append("")
        out.append("——————————")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Baholar / o'zlashtirish
# ---------------------------------------------------------------------------
async def fetch_performance(login: str, password: str) -> dict:
    """Grafik chizish uchun tayyor strukturali natija qaytaradi."""
    raw = _as_list(await hemis_request(login, password, "/education/performance"))

    subjects = []
    for item in raw:
        grade = _to_float(_first(item, "grade", "total_grade", "overallScore.percent"))
        max_grade = _to_float(_first(item, "max_grade", "overallScore.max_ball")) or 100.0
        subjects.append({
            "subject": _name_of(_first(item, "subject", "curriculumSubject")) or "Fan",
            "grade": grade,
            "max_grade": max_grade,
            "percent": round(grade / max_grade * 100, 1) if grade is not None and max_grade else None,
            "grade_name": _first(item, "grade_name", "gradeName", default=""),
            "credit": _to_float(_first(item, "credit", "subject.credit")),
            "absent_hours": _to_float(_first(item, "absent_on", "absentHours")) or 0,
        })

    graded = [s["percent"] for s in subjects if s["percent"] is not None]
    return {
        "subjects": subjects,
        "average_percent": round(sum(graded) / len(graded), 1) if graded else None,
        "total_subjects": len(subjects),
        "total_absent_hours": sum(s["absent_hours"] for s in subjects),
    }


def format_performance(data: dict) -> str:
    if not data["subjects"]:
        return "📊 Hozircha baholar va o'zlashtirish ma'lumotlari topilmadi."

    out = ["📊 **O'zlashtirish va Baholaringiz:**\n"]
    for s in data["subjects"]:
        ball = f"{s['grade']:g}" if s["grade"] is not None else "—"
        out.append(f"📚 **{s['subject']}**")
        out.append(f"   🔹 Ball: {ball} | Baho: {s['grade_name'] or 'Baholanmagan'}\n")
    if data["average_percent"] is not None:
        out.append(f"📈 **O'rtacha o'zlashtirish:** {data['average_percent']}%")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Eski kod bilan moslik (bot handlerlari o'zgarmasdan ishlashi uchun)
# ---------------------------------------------------------------------------
async def get_hemis_profile(login: str, password: str) -> str:
    try:
        return format_profile(await fetch_profile(login, password))
    except HemisError as e:
        return f"❌ {e.message}"


async def get_hemis_schedule(login: str, password: str) -> str:
    try:
        return format_schedule(await fetch_schedule(login, password))
    except HemisError as e:
        return f"❌ {e.message}"


async def get_hemis_grades_and_attendance(login: str, password: str) -> str:
    try:
        return format_performance(await fetch_performance(login, password))
    except HemisError as e:
        return f"❌ {e.message}"
