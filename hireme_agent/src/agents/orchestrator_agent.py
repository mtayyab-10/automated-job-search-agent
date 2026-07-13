"""
Orchestrator Agent — 9-Agent Career Co-Pilot Pipeline

  Agent 1 ── Search Agent       : live job search via Adzuna
  Agent 2 ── Scraper            : full job description extraction
  Agent 3 ── Gap Analyst        : match %, skill gaps, free learning resources
  Agent 4 ── ATS Analyser       : keyword scan, ATS score, optimised summary
  Agent 5 ── Writer Agent       : personalised cover letter
  Agent 6 ── Interview Agent    : 5 tailored Q&As per job
  Agent 7 ── Email Drafter      : cold + follow-up email pair
  Agent 8 ── Salary Intelligence: market fairness, negotiation script
  Agent 9 ── Career Roadmap     : 90-day action plan (runs once, across all jobs)

Status updates are streamed via an optional callback for live UI display.
"""

from src.memory import cv_store
from src.agents.hire_agent import derive_search_query, build_cover_letter
from src.agents.gap_analyst_agent import analyze_gap
from src.agents.ats_agent import analyze_ats
from src.agents.interview_agent import generate_interview_prep
from src.agents.email_agent import draft_emails
from src.agents.salary_agent import analyze_salary
from src.agents.roadmap_agent import generate_roadmap
from src.tools.job_search import search_jobs
from src.tools.job_scraper import scrape_job_listing


def run_orchestrator(location: str, count: int, status_callback=None) -> dict:
    """
    Master pipeline delegating to all 9 specialist agents.

    Args:
        location:         Target job location string.
        count:            Number of jobs to analyse.
        status_callback:  Optional callable(message: str) for live UI updates.

    Returns:
        {
            "jobs":    list of per-job result dicts,
            "roadmap": career roadmap dict (global, not per-job),
        }

    Raises:
        ValueError: If no CV has been loaded.
        RuntimeError: If the job search fails.
    """

    def _emit(msg: str):
        if status_callback:
            status_callback(msg)
        print(msg)

    # ── 0. Load CV ─────────────────────────────────────────────────────────────
    cv = cv_store.get_cv()
    if cv is None:
        raise ValueError("No CV loaded. Please upload your CV first.")

    candidate_name = cv.get("name", "Candidate")
    _emit(f"🧠 **Orchestrator:** CV loaded for **{candidate_name}**")

    # ── Agent 1: Search ────────────────────────────────────────────────────────
    query = derive_search_query(cv)
    _emit(f"🔍 **Search Agent:** Searching *'{query}'* in **{location or 'any location'}**…")

    search_count = max(int(count), 3)

    try:
        jobs = search_jobs(query=query, location=location, count=search_count)
    except Exception as e:
        _emit(f"❌ **Search Agent:** {e}")
        raise

    if not jobs and query != "software engineer":
        _emit(f"⚠️ No results for '{query}' — retrying with 'software engineer'…")
        try:
            jobs = search_jobs(query="software engineer", location=location, count=search_count)
        except Exception:
            jobs = []

    if not jobs and location:
        _emit(f"⚠️ No results in '{location}' — retrying without location filter…")
        try:
            jobs = search_jobs(query=query, location="", count=search_count)
        except Exception:
            jobs = []

    if not jobs:
        _emit("❌ **Search Agent:** No jobs found. Try a broader location or different role.")
        return {"jobs": [], "roadmap": {}}

    top_jobs = jobs[:3]
    _emit(f"✅ **Search Agent:** Found **{len(jobs)}** jobs — analysing top **{len(top_jobs)}**")

    # ── Per-job pipeline (Agents 2–8) ──────────────────────────────────────────
    job_results = []

    for idx, job in enumerate(top_jobs, start=1):
        job_title = job.get("title", "Unknown Role")
        company   = job.get("company_name", "Unknown Company")
        job_url   = job.get("url", "")

        _emit(f"\n─── **Job {idx}/{len(top_jobs)}: {job_title} @ {company}** ───")

        # Agent 2: Scraper
        _emit("   🌐 **Scraper:** Fetching full job description…")
        job_details = scrape_job_listing(job_url) if job_url else job.get("description", "")

        # Agent 3: Gap Analyst
        _emit("   📊 **Gap Analyst:** Scoring match & identifying skill gaps…")
        gap_data    = analyze_gap(cv, job, job_details)
        match_score = gap_data.get("match_score", 50)
        _emit(f"   ✅ Match score: **{match_score}%**")

        # Agent 4: ATS Analyser
        _emit("   🤖 **ATS Analyser:** Scanning keyword density…")
        ats_data  = analyze_ats(cv, job, job_details)
        ats_score = ats_data.get("ats_score", 60)
        _emit(f"   ✅ ATS score: **{ats_score}%**")

        # Agent 5: Writer
        _emit("   ✍️  **Writer Agent:** Crafting personalised cover letter…")
        cover_letter = build_cover_letter(cv, job, job_details)
        _emit("   ✅ Cover letter ready")

        # Agent 6: Interview Prep
        _emit("   🎤 **Interview Agent:** Generating tailored Q&As…")
        interview_prep = generate_interview_prep(cv, job, job_details)
        _emit(f"   ✅ {len(interview_prep)} questions prepared")

        # Agent 7: Email Drafter
        _emit("   📧 **Email Drafter:** Writing application + follow-up emails…")
        emails = draft_emails(cv, job, job_details)
        _emit("   ✅ Email pair ready")

        # Agent 8: Salary Intelligence
        _emit("   💰 **Salary Intelligence:** Analysing market fairness…")
        salary_data = analyze_salary(cv, job, job_details)
        verdict = salary_data.get("fairness_verdict", "Unknown")
        _emit(f"   ✅ Salary verdict: **{verdict}**")

        job_results.append({
            # Core job info
            "job_title":    job_title,
            "company":      company,
            "location":     job.get("location", ""),
            "salary":       job.get("salary_range", "Not specified"),
            "job_url":      job_url,
            "contract_type": job.get("contract_type", ""),
            "contract_time": job.get("contract_time", ""),
            # Agent 3: Gap
            "match_score":         match_score,
            "missing_skills":      gap_data.get("missing_skills", []),
            "candidate_strengths": gap_data.get("candidate_strengths", []),
            "learning_resources":  gap_data.get("learning_resources", []),
            # Agent 4: ATS
            "ats_score":           ats_score,
            "matched_keywords":    ats_data.get("matched_keywords", []),
            "missing_keywords":    ats_data.get("missing_keywords", []),
            "format_tips":         ats_data.get("format_tips", []),
            "optimised_summary":   ats_data.get("optimised_summary", ""),
            # Agent 5: Cover Letter
            "cover_letter":        cover_letter,
            # Agent 6: Interview
            "interview_prep":      interview_prep,
            # Agent 7: Emails
            "cold_email":          emails.get("cold_email", {}),
            "followup_email":      emails.get("followup_email", {}),
            # Agent 8: Salary
            "salary_intel":        salary_data,
        })

    # ── Agent 9: Career Roadmap (global, runs once) ────────────────────────────
    _emit("\n🗺️  **Career Roadmap Agent:** Building your personalised 90-day plan…")
    roadmap = generate_roadmap(cv, top_jobs)
    dream   = roadmap.get("dream_role", "")
    _emit(f"✅ **Roadmap ready!** Dream role: **{dream}**")

    _emit(f"\n🏁 **Orchestrator:** All 9 agents complete — **{len(job_results)} career packages** ready!")

    return {"jobs": job_results, "roadmap": roadmap}
