import os
import json
from groq import Groq
from models.schema import Need # pyright: ignore[reportMissingImports]
from datetime import datetime
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Extract disaster needs as JSON ONLY. No extra text.
Schema:
{
  "need_type": "food|medical|rescue|shelter|other",
  "location": "exact location or null",
  "urgency": 1-5,
  "summary": "brief description"
}"""


def extract_need(text: str, source: str = "social_media") -> Need:
    """Extract structured need from raw text using Groq LLM"""

    if not client:
        return None

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Text: {text}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=200
        )

        content = chat_completion.choices[0].message.content

        start = content.find('{')
        end   = content.rfind('}') + 1

        if start == -1 or end == 0:
            return None

        data = json.loads(content[start:end])
        data['source']    = source
        data['timestamp'] = datetime.now().isoformat()
        data['urgency']   = max(1, min(5, int(data.get('urgency', 3))))

        return Need(**data)

    except Exception:
        return None