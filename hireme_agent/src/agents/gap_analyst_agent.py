import json
import re
from google import genai
from src.config import settings


def analyze_gap(cv: dict, job: dict, job_details: str) -> dict:
    """
    Compares a candidate's CV against a job description using Gemini.
    Returns a dict with:
      - match_score (int 0-100)
      - missing_skills (list of strings)
      - candidate_strengths (list of strings)
      - learning_resources (list of {skill, resource, url})
    Falls back to a safe default dict on any failure.
    """
    default_result = {
        "match_score": 50,
        "missing_skills": [],
        "candidate_strengths": cv.get("skills", [])[:3],
        "learning_resources": [],
    }

    if not getattr(settings, "GEMINI_API_KEY", None):
        return default_result

    candidate_skills = ", ".join(cv.get("skills", []))
    candidate_experience = json.dumps(cv.get("experience", []))
    candidate_education = json.dumps(cv.get("education", []))
    job_title = job.get("title", "")
    company = job.get("company_name", "")

    prompt = (
        "You are an expert career coach and technical recruiter. "
        "Carefully compare the candidate's profile to the job description below.\n\n"
        "Return ONLY a raw JSON object — no markdown, no explanation, no code fences.\n\n"
        "The JSON must match exactly this structure:\n"
        "{\n"
        '  "match_score": <integer 0 to 100>,\n'
        '  "missing_skills": ["skill1", "skill2", ...],\n'
        '  "candidate_strengths": ["strength1", "strength2", ...],\n'
        '  "learning_resources": [\n'
        '    {"skill": "skill name", "resource": "resource title", "url": "https://..."}\n'
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- match_score must reflect genuine skill + experience alignment (be honest, not generous)\n"
        "- missing_skills: list up to 5 key skills required by the job but absent in the CV\n"
        "- candidate_strengths: list up to 4 genuine strengths from the CV that match this job\n"
        "- learning_resources: for each missing skill, suggest ONE free resource (Coursera, YouTube, "
        "official docs, freeCodeCamp, Kaggle, etc.) with a real URL\n\n"
        f"JOB TITLE: {job_title}\n"
        f"COMPANY: {company}\n"
        f"JOB DETAILS:\n{job_details[:1500]}\n\n"
        f"CANDIDATE SKILLS: {candidate_skills}\n"
        f"CANDIDATE EXPERIENCE: {candidate_experience}\n"
        f"CANDIDATE EDUCATION: {candidate_education}\n"
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        raw = (response.text or "").strip()

        # Strip any accidental markdown fences
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            raw = raw.strip()

        result = json.loads(raw)

        # Clamp match_score to valid range
        result["match_score"] = max(0, min(100, int(result.get("match_score", 50))))
        return result

    except Exception as e:
        print(f"Gap analyst agent error: {e}")
        return default_result
