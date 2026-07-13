"""
Diagnostic script — run this to find exactly where the pipeline breaks.
Usage (from hireme_agent/ directory):
    python debug_pipeline.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("HIREME AGENT — PIPELINE DIAGNOSTIC")
print("=" * 60)

# ── Step 1: Settings / .env ────────────────────────────────────
print("\n[1] Loading settings...")
try:
    from src.config import settings
    print(f"    ADZUNA_APP_ID  : {settings.ADZUNA_APP_ID[:6] if settings.ADZUNA_APP_ID else 'MISSING ❌'}***")
    print(f"    ADZUNA_APP_KEY : {settings.ADZUNA_APP_KEY[:6] if settings.ADZUNA_APP_KEY else 'MISSING ❌'}***")
    print(f"    ADZUNA_COUNTRY : {settings.ADZUNA_COUNTRY or 'MISSING ❌'}")
    print(f"    GEMINI_API_KEY : {'SET ✅' if settings.GEMINI_API_KEY else 'MISSING ❌'}")
except Exception as e:
    print(f"    ERROR: {e}")
    sys.exit(1)

# ── Step 2: Direct Adzuna API call ─────────────────────────────
print("\n[2] Testing Adzuna API directly...")
import requests

country = settings.ADZUNA_COUNTRY or "us"
url     = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
params  = {
    "app_id":           settings.ADZUNA_APP_ID,
    "app_key":          settings.ADZUNA_APP_KEY,
    "results_per_page": 3,
    "what":             "software engineer",
    "where":            "New York",
}
try:
    r = requests.get(url, params=params, timeout=15)
    print(f"    Status code: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"    Total results available: {data.get('count', 0)}")
        results = data.get("results", [])
        print(f"    Results in this page: {len(results)}")
        if results:
            print(f"    First job: {results[0].get('title')} @ {results[0].get('company', {}).get('display_name')}")
            print("    ✅ Adzuna API is WORKING")
        else:
            print("    ⚠️  API returned 0 results (check location/country)")
    else:
        print(f"    ❌ API error: {r.text[:200]}")
except Exception as e:
    print(f"    ❌ Request failed: {e}")

# ── Step 3: Test search_jobs function ──────────────────────────
print("\n[3] Testing search_jobs function...")
try:
    from src.tools.job_search import search_jobs
    jobs = search_jobs(query="software engineer", location="New York", count=3)
    print(f"    Jobs returned: {len(jobs)}")
    if jobs:
        print(f"    First job: {jobs[0].get('title')} @ {jobs[0].get('company_name')}")
        print("    ✅ search_jobs is WORKING")
    else:
        print("    ⚠️  search_jobs returned empty list")
except Exception as e:
    print(f"    ❌ search_jobs failed: {e}")

# ── Step 4: Test CV parsing ────────────────────────────────────
print("\n[4] Testing CV parsing with sample PDF...")

# Try both PDFs in docs/
docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
cv_candidates = [
    os.path.join(docs_dir, "cv-example-edinburgh-505577.min.pdf"),
    os.path.join(docs_dir, "good resume.pdf"),
]
cv_path = next((p for p in cv_candidates if os.path.exists(p)), None)

if cv_path:
    print(f"    Using CV file: {os.path.basename(cv_path)}")
    try:
        from src.parsers.cv_extractor import extract_text
        from src.parsers.cv_parser import parse_cv_text
        from src.memory import cv_store

        # FakeFile must implement .getvalue() — that's what cv_extractor calls
        with open(cv_path, "rb") as f:
            file_bytes = f.read()

        class FakeFile:
            def __init__(self, data: bytes, name: str):
                self._data = data
                self.name = name
            def getvalue(self) -> bytes:
                return self._data

        fake = FakeFile(file_bytes, os.path.basename(cv_path))
        raw_text = extract_text(fake)
        print(f"    Extracted text length: {len(raw_text)} chars")
        print(f"    First 200 chars: {raw_text[:200].strip()}")
        print("    ✅ CV extraction WORKING")

        # Also test full parse + store
        print("    Parsing CV with Gemini...")
        parsed = parse_cv_text(raw_text)
        cv_store.save_cv(parsed)
        print(f"    Parsed name    : {parsed.get('name', '?')}")
        print(f"    Skills found   : {parsed.get('skills', [])[:5]}")
        print(f"    Preferred roles: {parsed.get('preferred_roles', [])}")
        print(f"    Experience     : {[e.get('title') for e in parsed.get('experience', [])[:3]]}")

        from src.agents.hire_agent import derive_search_query
        query = derive_search_query(parsed)
        print(f"    Search query derived: '{query}'")
        print("    ✅ Full CV parse + query derivation WORKING")
    except Exception as e:
        print(f"    ❌ CV extraction/parsing failed: {e}")
        import traceback; traceback.print_exc()
else:
    print(f"    ⚠️  No CV PDF found in docs/ — checked: {cv_candidates}")

# ── Step 5: Test derive_search_query with manual CV ────────────
print("\n[5] Testing derive_search_query...")
try:
    from src.agents.hire_agent import derive_search_query
    test_cv = {
        "name": "John Smith",
        "skills": ["Python", "Django", "React", "SQL"],
        "experience": [{"title": "Software Engineer", "company": "ACME", "duration": "2 years"}],
        "preferred_roles": [],
    }
    query = derive_search_query(test_cv)
    print(f"    Query derived: '{query}'")
    print("    ✅ derive_search_query WORKING")
except Exception as e:
    print(f"    ❌ derive_search_query failed: {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
print("\nNEXT STEPS:")
print("  - If Step 2 fails: .env credentials are wrong")
print("  - If Step 2 works but Step 3 fails: settings not loading")
print("  - If Step 3 returns 0: the location you type doesn't match ADZUNA_COUNTRY")
print("  - IMPORTANT: ADZUNA_COUNTRY=us means only US locations work!")
print("    Try typing 'New York' or 'San Francisco' as the location in the app.")
