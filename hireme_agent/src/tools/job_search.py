import requests
import re
from src.config import settings

# Adzuna country codes that support job search
_COUNTRY_MAP = {
    # Keywords in location string → (adzuna_country_code, effective_where_param)
    # Empty effective_where = search all cities in that country (biggest pool)
    "pakistan":       ("gb", ""),   # Adzuna doesn't cover PK → GB full pool
    "karachi":        ("gb", ""),
    "lahore":         ("gb", ""),
    "islamabad":      ("gb", ""),
    "remote":         ("gb", ""),   # "Remote" → no location filter = biggest pool
    "global":         ("gb", ""),
    "anywhere":       ("gb", ""),
    "india":          ("in", ""),
    "mumbai":         ("in", "Mumbai"),
    "bangalore":      ("in", "Bangalore"),
    "bengaluru":      ("in", "Bangalore"),
    "delhi":          ("in", "Delhi"),
    "hyderabad":      ("in", "Hyderabad"),
    "united kingdom": ("gb", ""),
    "uk":             ("gb", ""),
    "london":         ("gb", "London"),
    "manchester":     ("gb", "Manchester"),
    "edinburgh":      ("gb", "Edinburgh"),
    "birmingham":     ("gb", "Birmingham"),
    "leeds":          ("gb", "Leeds"),
    "united states":  ("us", ""),
    "usa":            ("us", ""),
    "new york":       ("us", "New York"),
    "san francisco":  ("us", "San Francisco"),
    "chicago":        ("us", "Chicago"),
    "seattle":        ("us", "Seattle"),
    "austin":         ("us", "Austin"),
    "boston":         ("us", "Boston"),
    "canada":         ("ca", ""),
    "toronto":        ("ca", "Toronto"),
    "vancouver":      ("ca", "Vancouver"),
    "australia":      ("au", ""),
    "sydney":         ("au", "Sydney"),
    "melbourne":      ("au", "Melbourne"),
    "germany":        ("de", ""),
    "berlin":         ("de", "Berlin"),
    "france":         ("fr", ""),
    "paris":          ("fr", "Paris"),
    "netherlands":    ("nl", ""),
    "amsterdam":      ("nl", "Amsterdam"),
}


def _detect_country(location: str) -> tuple[str, str]:
    """
    Returns (adzuna_country_code, where_param) for a given location string.
    where_param is empty string when we want all jobs in that country (no city filter).
    """
    loc_lower = (location or "").lower().strip()

    for keyword, (code, where) in _COUNTRY_MAP.items():
        if keyword and keyword in loc_lower:
            print(f"[search_jobs] Matched '{keyword}' → country={code} where='{where or '(all)'}'")
            return code, where

    # Default: use env country, pass location as-is
    env_country = (settings.ADZUNA_COUNTRY or "gb").lower()
    return env_country, location.strip()


def _fmt_salary(val) -> str:
    try:
        return f"${int(float(val)):,}"
    except (TypeError, ValueError):
        return str(val)


def search_jobs(query: str, location: str, count: int) -> list:
    """
    Calls the Adzuna API with smart country auto-detection.
    Returns a list of clean job dicts. Raises on credential errors.
    """
    app_id  = settings.ADZUNA_APP_ID  or ""
    app_key = settings.ADZUNA_APP_KEY or ""

    if not app_id or not app_key:
        raise ValueError(
            "Adzuna API credentials are missing! "
            "Check that ADZUNA_APP_ID and ADZUNA_APP_KEY are in your .env file."
        )

    country, effective_location = _detect_country(location)
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id":           app_id,
        "app_key":          app_key,
        "results_per_page": max(int(count), 3),
        "what":             query,
        "content-type":     "application/json",
    }
    if effective_location:
        params["where"] = effective_location

    print(f"[search_jobs] country={country} location='{effective_location}' query='{query}'")

    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"[search_jobs] status={response.status_code}")

        if response.status_code != 200:
            print(f"[search_jobs] Error: {response.text[:300]}")
            return []

        data = response.json()
        raw  = data.get("results", [])
        print(f"[search_jobs] {len(raw)} results (total available: {data.get('count','?')})")

        jobs = []
        for item in raw:
            title        = re.sub(r"<[^>]*>", "", item.get("title", "")).strip()
            company_name = (item.get("company") or {}).get("display_name", "Not specified").strip()
            loc_name     = (item.get("location") or {}).get("display_name", "Not specified").strip()
            job_url      = item.get("redirect_url", "")

            sal_min = item.get("salary_min")
            sal_max = item.get("salary_max")
            if sal_min is not None and sal_max is not None:
                if abs(float(sal_min) - float(sal_max)) < 1:
                    salary_range = _fmt_salary(sal_min)
                else:
                    salary_range = f"{_fmt_salary(sal_min)} – {_fmt_salary(sal_max)}"
            elif sal_min is not None:
                salary_range = f"From {_fmt_salary(sal_min)}"
            elif sal_max is not None:
                salary_range = f"Up to {_fmt_salary(sal_max)}"
            else:
                salary_range = "Not specified"

            clean_desc = re.sub(r"<[^>]*>", "", item.get("description", "")).strip()
            clean_desc = re.sub(r"\s+", " ", clean_desc)[:800]

            jobs.append({
                "id":            str(item.get("id", "")),
                "title":         title,
                "company_name":  company_name,
                "location":      loc_name,
                "salary_range":  salary_range,
                "description":   clean_desc,
                "url":           job_url,
                "contract_type": item.get("contract_type", ""),
                "contract_time": item.get("contract_time", ""),
                "adzuna_country": country,
            })

        return jobs

    except ValueError:
        raise
    except Exception as e:
        print(f"[search_jobs] Exception: {e}")
        raise RuntimeError(f"Job search failed: {e}") from e
