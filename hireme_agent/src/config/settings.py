import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve the .env path: this file is at src/config/settings.py
# So parent = config, parent.parent = src, parent.parent.parent = hireme_agent (project root)
_here = Path(__file__).resolve()
_project_root = _here.parent.parent.parent   # hireme_agent/
_env_path = _project_root / ".env"

# Also try one level up in case running from a different cwd
if not _env_path.exists():
    _env_path = _project_root.parent / ".env"

load_dotenv(dotenv_path=_env_path, override=True)

# Debug: print path on startup so we can confirm it loads
_loaded = _env_path.exists()
print(f"[settings] .env path: {_env_path} | exists: {_loaded}")

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "").strip()
ADZUNA_APP_ID   = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY  = os.getenv("ADZUNA_APP_KEY", "").strip()
ADZUNA_COUNTRY  = os.getenv("ADZUNA_COUNTRY", "us").strip().lower()

print(f"[settings] ADZUNA_APP_ID={ADZUNA_APP_ID[:6]}*** | COUNTRY={ADZUNA_COUNTRY} | GEMINI={'set' if GEMINI_API_KEY else 'MISSING'}")
