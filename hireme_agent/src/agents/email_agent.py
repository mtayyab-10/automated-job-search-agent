"""
Email Drafter Agent.

Generates two ready-to-send emails for each job opportunity:
  1. Cold application email (when applying directly, not via a portal)
  2. Post-application follow-up email (to send 5-7 days after applying)
"""

import json
import re
from google import genai
from src.config import settings


def draft_emails(cv: dict, job: dict, job_details: str) -> dict:
    """
    Generates a cold application email and a follow-up email for a specific job.

    Args:
        cv:          Parsed candidate CV dict.
        job:         Job dict (title, company_name, location, salary_range, url).
        job_details: Full scraped job description text.

    Returns:
        {
            "cold_email":   {"subject": str, "body": str},
            "followup_email": {"subject": str, "body": str},
        }
    """
    candidate_name = cv.get("name", "the candidate")
    candidate_email = cv.get("email", "")
    skills_top = ", ".join(cv.get("skills", [])[:5])
    job_title = job.get("title", "the role")
    company = job.get("company_name", "your company")

    fallback = {
        "cold_email": {
            "subject": f"Application for {job_title} — {candidate_name}",
            "body": (
                f"Dear Hiring Team,\n\n"
                f"I am writing to express my strong interest in the {job_title} position at {company}. "
                f"With expertise in {skills_top}, I am confident I can make an immediate contribution.\n\n"
                f"I have attached my CV for your review and would welcome the opportunity to discuss "
                f"how my background aligns with your team's needs.\n\n"
                f"Thank you for your time.\n\nBest regards,\n{candidate_name}"
            ),
        },
        "followup_email": {
            "subject": f"Following up — {job_title} Application — {candidate_name}",
            "body": (
                f"Dear Hiring Team,\n\n"
                f"I wanted to follow up on my application for the {job_title} role at {company}, "
                f"submitted last week. I remain very enthusiastic about this opportunity and "
                f"the chance to bring my skills in {skills_top} to your team.\n\n"
                f"Please let me know if you need any additional information. "
                f"I look forward to hearing from you.\n\nBest regards,\n{candidate_name}"
            ),
        },
    }

    if not getattr(settings, "GEMINI_API_KEY", None):
        return fallback

    prompt = (
        "You are an expert career coach writing professional job application emails.\n\n"
        "Generate TWO emails for this candidate applying to this specific job.\n\n"
        "Return ONLY a raw JSON object — no markdown, no explanation, no code fences.\n\n"
        "JSON structure:\n"
        "{\n"
        '  "cold_email": {\n'
        '    "subject": "...",\n'
        '    "body": "full email body with Dear...\\n\\n...\\n\\nBest regards,\\n[name]"\n'
        "  },\n"
        '  "followup_email": {\n'
        '    "subject": "...",\n'
        '    "body": "full follow-up email body"\n'
        "  }\n"
        "}\n\n"
        "Rules for cold_email:\n"
        "- Professional, warm, confident tone\n"
        "- 3 short paragraphs: hook → value → call to action\n"
        "- Mention 2-3 specific skills from the CV that match this role\n"
        "- Never sound desperate or generic\n"
        "- Subject line must be specific and attention-grabbing\n\n"
        "Rules for followup_email:\n"
        "- Send 5-7 days after applying\n"
        "- Brief, polite, shows continued enthusiasm\n"
        "- Max 3 sentences in the body\n"
        "- Slightly different angle — mention one specific thing about the company/role\n\n"
        f"CANDIDATE NAME: {candidate_name}\n"
        f"CANDIDATE EMAIL: {candidate_email}\n"
        f"TOP SKILLS: {skills_top}\n"
        f"CV SUMMARY: {cv.get('summary', '')}\n\n"
        f"JOB TITLE: {job_title}\n"
        f"COMPANY: {company}\n"
        f"LOCATION: {job.get('location', '')}\n"
        f"JOB DETAILS:\n{job_details[:1200]}\n"
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
        # Validate structure
        if "cold_email" in result and "followup_email" in result:
            return result
        return fallback

    except Exception as e:
        print(f"Email drafter agent error: {e}")
        return fallback
