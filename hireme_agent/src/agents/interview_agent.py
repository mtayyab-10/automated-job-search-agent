import json
import re
from google import genai
from src.config import settings


def generate_interview_prep(cv: dict, job: dict, job_details: str) -> list:
    """
    Generates 5 tailored interview questions and model answers for a specific job,
    personalised to the candidate's CV.
    Returns a list of dicts: [{question, model_answer, category}]
    Falls back to generic questions on failure.
    """
    fallback = [
        {
            "question": f"Why are you interested in this {job.get('title', 'role')} position?",
            "model_answer": (
                f"I'm excited about this role because it aligns well with my background in "
                f"{', '.join(cv.get('skills', ['software development'])[:3])}. "
                "I'm looking for an opportunity to apply my skills in a meaningful way and grow professionally."
            ),
            "category": "Motivation",
        },
        {
            "question": "Tell me about yourself.",
            "model_answer": (
                f"I'm {cv.get('name', 'a candidate')} with experience in "
                f"{', '.join(cv.get('skills', ['various technologies'])[:4])}. "
                f"{cv.get('summary', 'I am passionate about technology and solving real-world problems.')}"
            ),
            "category": "Introduction",
        },
        {
            "question": "What is your greatest professional strength?",
            "model_answer": (
                f"One of my key strengths is {cv.get('skills', ['problem-solving'])[0] if cv.get('skills') else 'problem-solving'}. "
                "I've consistently applied this across different projects and teams to deliver results."
            ),
            "category": "Strengths",
        },
        {
            "question": "Describe a challenging project you worked on.",
            "model_answer": (
                "In a previous role, I was tasked with delivering a complex feature under a tight deadline. "
                "I broke the problem into smaller milestones, collaborated with my team, and we delivered on time."
            ),
            "category": "Behavioural",
        },
        {
            "question": "Where do you see yourself in 5 years?",
            "model_answer": (
                "I see myself growing into a senior technical role where I can mentor others and lead impactful projects. "
                "I'm excited about the trajectory this company offers."
            ),
            "category": "Career Goals",
        },
    ]

    if not getattr(settings, "GEMINI_API_KEY", None):
        return fallback

    candidate_name = cv.get("name", "the candidate")
    candidate_skills = ", ".join(cv.get("skills", []))
    candidate_experience = json.dumps(cv.get("experience", []))
    job_title = job.get("title", "")
    company = job.get("company_name", "")

    prompt = (
        "You are an expert interview coach preparing a candidate for a specific job interview.\n\n"
        "Generate exactly 5 interview questions that a real interviewer would ask for this specific role, "
        "and write a strong model answer for each question, personalised to this specific candidate's background.\n\n"
        "Return ONLY a raw JSON array — no markdown, no explanation, no code fences.\n\n"
        "Each item must follow this exact structure:\n"
        "[\n"
        '  {"question": "...", "model_answer": "...", "category": "Technical|Behavioural|Motivation|Strengths|Culture Fit"}\n'
        "]\n\n"
        "Rules:\n"
        "- Mix question types: include at least 2 technical, 1 behavioural (STAR format), 1 motivation, 1 other\n"
        "- Model answers must reference the candidate's ACTUAL skills and experience, not be generic\n"
        "- Keep each answer concise but impressive (3-5 sentences)\n"
        "- Use confident, professional language\n\n"
        f"CANDIDATE NAME: {candidate_name}\n"
        f"CANDIDATE SKILLS: {candidate_skills}\n"
        f"CANDIDATE EXPERIENCE: {candidate_experience}\n\n"
        f"JOB TITLE: {job_title}\n"
        f"COMPANY: {company}\n"
        f"JOB DETAILS:\n{job_details[:1500]}\n"
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        raw = (response.text or "").strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            raw = raw.strip()

        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) > 0:
            return questions[:5]
        return fallback

    except Exception as e:
        print(f"Interview prep agent error: {e}")
        return fallback
