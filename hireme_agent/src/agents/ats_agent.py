"""
ATS (Applicant Tracking System) Analyser Agent.

Many companies run CVs through automated ATS software before a human ever
reads them. This agent scores how well the CV would survive that filter
for a specific job and returns actionable keyword recommendations.
"""

import json
import re
from google import genai
from src.config import settings


def analyze_ats(cv_raw_text_or_dict, job: dict, job_details: str) -> dict:
    """
    Analyses ATS compatibility between a CV and a specific job posting.

    Args:
        cv_raw_text_or_dict: Either the parsed CV dict or raw CV text.
        job:                 Job dict with title, company_name, etc.
        job_details:         Full scraped job description text.

    Returns:
        {
            "ats_score":             int (0-100),
            "matched_keywords":      list[str],
            "missing_keywords":      list[str],
            "format_tips":           list[str],
            "optimised_summary":     str  (rewritten 2-sentence summary for this job),
        }
    """
    default = {
        "ats_score": 60,
        "matched_keywords": [],
        "missing_keywords": [],
        "format_tips": [
            "Use standard section headings (Experience, Education, Skills)",
            "Avoid tables, columns, headers/footers — ATS can't parse them",
            "Use plain bullet points, not symbols or icons",
        ],
        "optimised_summary": "",
    }

    if not getattr(settings, "GEMINI_API_KEY", None):
        return default

    # Support both dict and raw text input
    if isinstance(cv_raw_text_or_dict, dict):
        cv_skills = ", ".join(cv_raw_text_or_dict.get("skills", []))
        cv_summary = cv_raw_text_or_dict.get("summary", "")
        cv_experience = json.dumps(cv_raw_text_or_dict.get("experience", []))
        cv_education = json.dumps(cv_raw_text_or_dict.get("education", []))
        cv_text_block = (
            f"Skills: {cv_skills}\n"
            f"Summary: {cv_summary}\n"
            f"Experience: {cv_experience}\n"
            f"Education: {cv_education}"
        )
    else:
        cv_text_block = str(cv_raw_text_or_dict)[:2000]

    prompt = (
        "You are an expert ATS (Applicant Tracking System) analyst. "
        "Your job is to determine how well this CV would pass automated screening for this specific job.\n\n"
        "Return ONLY a raw JSON object — no markdown, no explanation, no code fences.\n\n"
        "JSON structure:\n"
        "{\n"
        '  "ats_score": <integer 0-100>,\n'
        '  "matched_keywords": ["keyword1", ...],\n'
        '  "missing_keywords": ["keyword1", ...],\n'
        '  "format_tips": ["tip1", ...],\n'
        '  "optimised_summary": "2-sentence summary that maximises ATS score for this specific role"\n'
        "}\n\n"
        "Rules:\n"
        "- ats_score: how many % of the key ATS-detectable keywords/phrases are present in the CV\n"
        "- matched_keywords: up to 8 important role-specific keywords ALREADY in the CV\n"
        "- missing_keywords: up to 6 high-impact keywords the JD uses that are ABSENT from the CV\n"
        "- format_tips: 2-3 specific formatting improvements to improve ATS parsing\n"
        "- optimised_summary: rewrite the candidate's summary to include the top missing keywords "
        "naturally, tailored to this specific role\n\n"
        f"JOB TITLE: {job.get('title', '')}\n"
        f"COMPANY: {job.get('company_name', '')}\n"
        f"JOB DESCRIPTION:\n{job_details[:1500]}\n\n"
        f"CANDIDATE CV:\n{cv_text_block}\n"
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        raw = (response.text or "").strip()

        if raw.startswith("```"):
            raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            raw = raw.strip()

        result = json.loads(raw)
        result["ats_score"] = max(0, min(100, int(result.get("ats_score", 60))))
        return result

    except Exception as e:
        print(f"ATS analyser error: {e}")
        return default
