import json
from services.gemini_service import ask_gemini


def extract_skills(resume_text):
    prompt = f"""
You are a Skill Extraction Agent.

Read this resume and extract all technical and professional skills.

Return ONLY a valid JSON object with exactly these keys:
- skills_list (array of skill name strings, e.g. ["Python", "SQL", "React"])
- skills_text (comma-separated string of all skills, e.g. "Python, SQL, React")

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
            "skills_list": [],
            "skills_text": raw
        }
