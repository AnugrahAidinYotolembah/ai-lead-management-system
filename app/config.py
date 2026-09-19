import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def get_database_url():
    db_path = os.getenv("DATABASE_PATH", str(BASE_DIR / "leads.db"))
    return f"sqlite:///{db_path}"

DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "leads.db"))
DATABASE_URL = get_database_url()

# Seed data paths
SEED_CSV_PATH = BASE_DIR / "data" / "leads_seed.csv"
SEED_JSON_PATH = BASE_DIR / "data" / "website_form_submissions.json"

# AI / LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto") # "openrouter", "openai", "gemini", or "local"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Supported standard statuses
STANDARD_STATUSES = [
    "New",
    "Qualified",
    "Contacted",
    "Connected",
    "Opportunity",
    "Closed Won",
    "Closed Lost",
]

# Supported standard channels
STANDARD_CHANNELS = [
    "Website",
    "Event",
    "LinkedIn",
    "Organic Search",
    "Referral",
    "Manual/Sales",
    "Other",
]
