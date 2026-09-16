import anthropic
from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

async def ask_claude_for_ppt(topic: str) -> str:
    """Claude orqali taqdimot (PPT) matnini va strukturasini shakllantirish"""
    try:
        system_instruction = (
            "Siz mukammal taqdimot (Presentation) tayyorlovchi yordamchisiz. "
            "Berilgan mavzuni mantiqiy qismlarga (Kirish, Asosiy qism, Xulosa) bo'ling. "
            "Har bir slayd uchun qisqa tezislar (bullet points) yozing. Matn ilmiy, tushunarli va o'zbek tilida bo'lsin."
        )

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            system=system_instruction,
            messages=[
                {"role": "user", "content": f"Mavzu: {topic}\nIltimos, shu mavzuda taqdimot matni va slaydlar tuzilmasini tayyorlab ber."}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Claude tizimida xatolik: {str(e)}"
