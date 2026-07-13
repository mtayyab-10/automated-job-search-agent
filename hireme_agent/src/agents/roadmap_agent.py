"""
Career Roadmap Agent — the most out-of-the-box feature.

Instead of just matching today's jobs, this agent looks at the candidate's
current profile and generates a personalised 90-day career acceleration plan:

  - What to build (projects)
  - What to learn (skills with deadlines)
  - Who to connect with on LinkedIn (roles/titles to target)
  - What certifications to get (ranked by ROI)
  - A "dream role" 12-month target based on trajectory

This is the feature NO other team will have.
"""

import json
import re
from google import genai
from src.config import settings


def generate_roadmap(cv: dict, target_jobs: list) -> dict:
    """
    Generates a personalised 90-day career acceleration roadmap.

    Args:
        cv:          Parsed candidate CV dict.
        target_jobs: List of job dicts from the search results (title, company, etc.)

    Returns:
        {
            "dream_role":         str,
            "readiness_score":    int (0-100, how ready they are NOW for the dream role),
            "week_1_4":           list[str]  (4 weekly actions),
            "week_5_8":           list[str],
            "week_9_12":          list[str],
            "top_certifications": list[{name, provider, url, time_weeks, roi_reason}],
            "portfolio_projects": list[{title, description, tech_stack, impact}],
            "linkedin_targets":   list[str]  (job titles to connect with),
            "power_move":         str  (one bold unconventional action),
        }
    """
    default = {
        "dream_role": "Senior Software Engineer",
        "readiness_score": 55,
        "week_1_4": [
            "Polish your CV to ATS standards",
            "Build a GitHub portfolio with 2 complete projects",
            "Connect with 10 engineers at target companies on LinkedIn",
            "Complete one free certification on Coursera",
        ],
        "week_5_8": [
            "Contribute to one open-source project",
            "Write a technical blog post demonstrating your expertise",
            "Apply to 5 target roles with personalised cover letters",
            "Do 3 mock technical interviews on Pramp or interviewing.io",
        ],
        "week_9_12": [
            "Follow up on all applications",
            "Negotiate salary using market data",
            "Build your personal brand on LinkedIn with weekly posts",
            "Get one referral from your network at a target company",
        ],
        "top_certifications": [
            {
                "name": "AWS Certified Solutions Architect",
                "provider": "Amazon",
                "url": "https://aws.amazon.com/certification/",
                "time_weeks": 8,
                "roi_reason": "Increases salary by 15-20% on average",
            }
        ],
        "portfolio_projects": [
            {
                "title": "Full-Stack Web Application",
                "description": "Build and deploy a complete app with authentication, database, and API",
                "tech_stack": "React, Node.js, PostgreSQL, Docker",
                "impact": "Demonstrates end-to-end capability to employers",
            }
        ],
        "linkedin_targets": [
            "Engineering Manager",
            "Senior Software Engineer",
            "Tech Lead",
            "CTO at startup",
        ],
        "power_move": (
            "Reach out directly to the CTO or VP Engineering of your top 3 target companies "
            "with a 3-sentence personalised message showing you know their tech stack. "
            "85% of jobs are filled through networking, not job boards."
        ),
    }

    if not getattr(settings, "GEMINI_API_KEY", None):
        return default

    skills = ", ".join(cv.get("skills", []))
    experience_json = json.dumps(cv.get("experience", []))
    education_json = json.dumps(cv.get("education", []))
    target_roles = ", ".join(j.get("title", "") for j in target_jobs[:3])
    companies = ", ".join(j.get("company_name", "") for j in target_jobs[:3])

    prompt = (
        "You are an elite career strategist who has helped engineers land roles at FAANG, unicorns, "
        "and top startups. Create a hyper-personalised 90-day career acceleration roadmap.\n\n"
        "Return ONLY a raw JSON object — no markdown, no explanation, no code fences.\n\n"
        "JSON structure:\n"
        "{\n"
        '  "dream_role": "specific role title this candidate should target in 12 months",\n'
        '  "readiness_score": <integer 0-100, honest assessment of how ready they are NOW>,\n'
        '  "week_1_4": ["action1", "action2", "action3", "action4"],\n'
        '  "week_5_8": ["action1", "action2", "action3", "action4"],\n'
        '  "week_9_12": ["action1", "action2", "action3", "action4"],\n'
        '  "top_certifications": [\n'
        '    {"name": "...", "provider": "...", "url": "https://...", "time_weeks": 4, "roi_reason": "..."}\n'
        "  ],\n"
        '  "portfolio_projects": [\n'
        '    {"title": "...", "description": "...", "tech_stack": "...", "impact": "..."}\n'
        "  ],\n"
        '  "linkedin_targets": ["job title to connect with", ...],\n'
        '  "power_move": "one bold, unconventional career move specific to this candidate"\n'
        "}\n\n"
        "Rules:\n"
        "- Every action must be SPECIFIC and ACTIONABLE — no vague advice like 'improve your skills'\n"
        "- dream_role must be 1-2 levels above their current level\n"
        "- week_1_4 actions: quick wins that take less than 1 week each\n"
        "- week_5_8 actions: medium effort, skill-building focus\n"
        "- week_9_12 actions: application, networking, and closing\n"
        "- top_certifications: max 3, ranked by salary ROI, with REAL provider URLs\n"
        "- portfolio_projects: max 2, highly specific to THIS candidate's skill gaps and target roles\n"
        "- power_move: something genuinely clever and bold that 95% of candidates won't do\n\n"
        f"CANDIDATE SKILLS: {skills}\n"
        f"CANDIDATE EXPERIENCE: {experience_json}\n"
        f"CANDIDATE EDUCATION: {education_json}\n"
        f"CANDIDATE SUMMARY: {cv.get('summary', '')}\n\n"
        f"TARGET ROLES (from search): {target_roles}\n"
        f"TARGET COMPANIES: {companies}\n"
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
        result["readiness_score"] = max(0, min(100, int(result.get("readiness_score", 55))))
        return result

    except Exception as e:
        print(f"Career roadmap agent error: {e}")
        return default
