import json
from services.gemini_service import ask_gemini


def analyze_resume(resume_text):
    prompt = f"""
You are a Resume Analysis Agent.

Analyze this resume and extract the following information.

Return ONLY a valid JSON object with exactly these keys:
- name (string)
- email (string or null)
- phone (string or null)
- experience (string, e.g. "3 years" or "2 years 6 months")
- education (string, highest qualification)
- ai_summary (2-3 sentence professional summary of the candidate)

Resume:
{resume_text}

Return only the JSON object. No explanation, no markdown, no code fences.
"""
    raw = ask_gemini(prompt)

    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except Exception:
        return {
            "name": None,
            "email": None,
            "phone": None,
            "experience": None,
            "education": None,
            "ai_summary": raw
        }
