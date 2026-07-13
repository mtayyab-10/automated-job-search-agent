import json
import re
from google import genai
from src.config import settings
from src.memory import cv_store
from src.tools.job_search import search_jobs
from src.tools.job_scraper import scrape_job_listing


ROLE_KEYWORDS = [
    "software engineer",
    "data analyst",
    "data scientist",
    "machine learning engineer",
    "ai engineer",
    "backend developer",
    "frontend developer",
    "full stack developer",
    "web developer",
    "mobile developer",
    "product manager",
    "project manager",
    "devops engineer",
    "cloud engineer",
    "business analyst",
    "cyber security analyst",
    "qa engineer",
    "tester",
    "ui ux designer",
    "graphic designer",
    "accountant",
    "marketing specialist",
    "sales representative",
    "hr specialist",
    "research assistant",
    "teacher",
    "intern",
]


def derive_search_query(cv: dict) -> str:
    preferred_roles = cv.get("preferred_roles", []) or []
    if preferred_roles:
        return str(preferred_roles[0]).strip()

    experience = cv.get("experience", []) or []
    for item in experience:
        title = str(item.get("title", "")).strip().lower()
        for role in ROLE_KEYWORDS:
            if role in title:
                return role

    skills = cv.get("skills", []) or []
    if skills:
        joined_skills = " ".join(str(skill).lower() for skill in skills)
        if any(keyword in joined_skills for keyword in ["python", "django", "flask", "fastapi", "react", "node", "sql"]):
            if "python" in joined_skills:
                return "python developer"
            if any(keyword in joined_skills for keyword in ["django", "flask", "fastapi"]):
                return "backend developer"
            if "react" in joined_skills:
                return "frontend developer"
            if "sql" in joined_skills:
                return "data analyst"
        return str(skills[0]).strip()

    summary = str(cv.get("summary", "")).strip()
    if summary:
        lower_summary = summary.lower()
        for role in ROLE_KEYWORDS:
            if role in lower_summary:
                return role
        words = summary.split()
        return " ".join(words[:2]) if len(words) >= 2 else words[0]

    return "software engineer"


def build_cover_letter(cv: dict, job: dict, job_details: str) -> str:
    base_prompt = (
        "Write a tailored cover letter using only the candidate information and job details provided. "
        "Return exactly 3 paragraphs, plain text only, no markdown, no bullet points. "
        "Do not invent experience or skills. Keep the tone professional and warm."
    )

    if getattr(settings, "GEMINI_API_KEY", None):
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=(
                    f"{base_prompt}\n\n"
                    f"Candidate Name: {cv.get('name', 'Unknown')}\n"
                    f"Candidate Summary: {cv.get('summary', '')}\n"
                    f"Candidate Skills: {', '.join(cv.get('skills', []))}\n"
                    f"Candidate Experience: {json.dumps(cv.get('experience', []))}\n"
                    f"Candidate Education: {json.dumps(cv.get('education', []))}\n\n"
                    f"Job Title: {job.get('title', '')}\n"
                    f"Company: {job.get('company_name', '')}\n"
                    f"Location: {job.get('location', '')}\n"
                    f"Salary: {job.get('salary_range', '')}\n"
                    f"Job Details: {job_details}\n"
                ),
            )
            text = (response.text or "").strip()
            if text:
                return text
        except Exception as e:
            print(f"Gemini cover letter generation failed, using template fallback: {e}")

    skills = ", ".join(cv.get("skills", [])[:5]) or "relevant skills"
    candidate_name = cv.get("name", "the candidate")
    job_title = job.get("title", "the role")
    company_name = job.get("company_name", "your company")
    location = job.get("location", "the advertised location")

    return (
        f"Dear Hiring Manager,\n\n"
        f"I am writing to express my interest in the {job_title} position at {company_name}. "
        f"With a background summarized by {candidate_name} and skills including {skills}, I am confident in my ability to contribute value to your team.\n\n"
        f"My experience and capabilities align well with the requirements of this role in {location}. "
        f"I would welcome the opportunity to bring my strengths to {company_name} and support your team’s goals.\n\n"
        f"Thank you for your time and consideration. I would be grateful for the opportunity to discuss how I can contribute to your organization."
    )

def run_agent(location: str, count: int) -> list:
    """
    Accepts a location string and result count integer.
    Loads the CV from cv_store and raises a ValueError if missing.
    Orchestrates the job search, scraping, and cover letter writing loop.
    Returns a list of parsed result dictionaries.
    """
    # Load the CV from cv_store
    cv = cv_store.get_cv()
    if cv is None:
        raise ValueError("No CV has been loaded yet. Please ingest a CV first.")

    query = derive_search_query(cv)
    print(f"Using search query: {query}")

    search_count = max(int(count), 3)
    jobs = search_jobs(query=query, location=location, count=search_count)
    if not jobs and query != "software engineer":
        fallback_query = "software engineer"
        print(f"No jobs found for '{query}'. Retrying with fallback query '{fallback_query}'.")
        jobs = search_jobs(query=fallback_query, location=location, count=search_count)
    if not jobs:
        return []

    top_jobs = jobs[:3]
    results = []

    for job in top_jobs:
        job_url = job.get("url", "")
        job_details = scrape_job_listing(job_url) if job_url else job.get("description", "")
        cover_letter = build_cover_letter(cv, job, job_details)

        results.append({
            "job_title": job.get("title", "Unknown Job Title"),
            "company": job.get("company_name", "Unknown Company"),
            "location": job.get("location", "Unknown Location"),
            "salary": job.get("salary_range", "Not specified"),
            "job_url": job_url,
            "cover_letter": cover_letter,
        })

    return results
