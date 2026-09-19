import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# On Vercel serverless environment, filesystem is read-only except /tmp
# We copy leads.db into /tmp if running in production serverless
if os.environ.get("VERCEL") == "1":
    tmp_db = Path("/tmp/leads.db")
    local_db = BASE_DIR / "leads.db"
    if not tmp_db.exists() and local_db.exists():
        shutil.copyfile(str(local_db), str(tmp_db))
    os.environ["DATABASE_PATH"] = "/tmp/leads.db"

from app.main import app
