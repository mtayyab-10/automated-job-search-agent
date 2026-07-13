"""
Salary Intelligence Agent.

Goes beyond basic job matching — analyses salary fairness for the candidate
based on their experience level, location, and skills. Tells the candidate:
  - Whether the posted salary is fair vs. market rate
  - Exact negotiation talking points  
  - Counter-offer range to ask for
  - LinkedIn salary benchmark context
"""

import json
import re
from google import genai
from src.config import settings


def analyze_salary(cv: dict, job: dict, job_details: str) -> dict:
    """
    Generates salary intelligence: market fairness, negotiation script,
    and a counter-offer range.

    Returns:
        {
            "posted_salary":         str,
            "market_low":            str,
            "market_high":           str,
            "fairness_verdict":      str  ("Below Market" | "Fair" | "Above Market"),
            "fairness_pct":          int  (how % above/below market the offer is),
            "experience_years":      int,
            "seniority_level":       str,
            "negotiation_script":    str  (3-4 sentences to say in negotiation),
            "counter_offer_range":   str,
            "key_talking_points":    list[str],
        }
    """
    posted = job.get("salary_range", "Not specified")
    location = job.get("location", "")
    job_title = job.get("title", "the role")
    company = job.get("company_name", "")
    skills = ", ".join(cv.get("skills", []))
    experience = json.dumps(cv.get("experience", []))

    default = {
        "posted_salary":       posted,
        "market_low":          "Not available",
        "market_high":         "Not available",
        "fairness_verdict":    "Unknown",
        "fairness_pct":        0,
        "experience_years":    0,
        "seniority_level":     "Mid-level",
        "negotiation_script":  (
            "Thank you for the offer. Based on my research into market rates for this role "
            "in this location, and considering my specific experience with "
            f"{cv.get('skills', ['relevant technologies'])[0] if cv.get('skills') else 'these technologies'}, "
            "I was hoping we could discuss a slightly higher figure. "
            "I'm very excited about this opportunity and want to make this work for both of us."
        ),
        "counter_offer_range": "Negotiate based on market data",
        "key_talking_points":  [
            f"Highlight expertise in {skills[:100]}",
            "Reference specific impact from previous roles",
            "Express strong interest while anchoring to market rate",
        ],
    }

    if not getattr(settings, "GEMINI_API_KEY", None):
        return default

    prompt = (
        "You are a top compensation consultant with deep knowledge of tech salary benchmarks globally.\n\n"
        "Analyse the salary situation for this candidate applying to this specific job.\n\n"
        "Return ONLY a raw JSON object — no markdown, no explanation, no code fences.\n\n"
        "JSON structure:\n"
        "{\n"
        '  "posted_salary": "the salary from the job posting or \'Not disclosed\'",\n'
        '  "market_low": "low end of fair market range for this role/location (e.g. $85,000)",\n'
        '  "market_high": "high end of fair market range (e.g. $130,000)",\n'
        '  "fairness_verdict": "Below Market | Fair | Above Market",\n'
        '  "fairness_pct": <integer: how many % the offer is above(+) or below(-) mid-market>,\n'
        '  "experience_years": <estimated years of experience from CV, integer>,\n'
        '  "seniority_level": "Junior | Mid-level | Senior | Lead | Principal",\n'
        '  "negotiation_script": "3-4 confident sentences the candidate should say when negotiating, '
        'referencing their specific skills and this role",\n'
        '  "counter_offer_range": "e.g. $95,000 – $110,000",\n'
        '  "key_talking_points": ["point1", "point2", "point3"]\n'
        "}\n\n"
        "Rules:\n"
        "- Use real-world salary data for this role + location (US/UK market knowledge)\n"
        "- Be specific — no vague ranges\n"
        "- The negotiation_script must reference THIS candidate's actual skills\n"
        "- key_talking_points: 3 concrete things to say in the salary negotiation meeting\n\n"
        f"JOB TITLE: {job_title}\n"
        f"COMPANY: {company}\n"
        f"LOCATION: {location}\n"
        f"POSTED SALARY: {posted}\n"
        f"JOB DETAILS: {job_details[:800]}\n\n"
        f"CANDIDATE SKILLS: {skills}\n"
        f"CANDIDATE EXPERIENCE: {experience}\n"
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
        result["fairness_pct"] = int(result.get("fairness_pct", 0))
        return result

    except Exception as e:
        print(f"Salary intelligence error: {e}")
        return default
