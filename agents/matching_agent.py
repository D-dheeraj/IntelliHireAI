import json
from services.gemini_service import ask_gemini


def match_candidate(skills_text, job_description):
    prompt = f"""
You are a Job Matching Agent.

Compare the candidate's skills against the job description below.

Candidate skills:
{skills_text}

Job description:
{job_description}

Return ONLY a valid JSON object with exactly these keys:
- match_score (integer between 0 and 100)
- matched_skills (array of skill strings that match the job)
- missing_skills (array of skill strings the candidate lacks)
- recommendation (string: "Strong Hire", "Hire", "Maybe", or "No Hire")
- match_summary (2-3 sentence explanation of the match)

Return only the JSON object. No explanation, no markdown, no code fences.
"""
    raw = ask_gemini(prompt)

    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except Exception:
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "recommendation": "Maybe",
            "match_summary": raw
        }
