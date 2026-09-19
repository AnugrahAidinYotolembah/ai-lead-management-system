import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Lead
from app.services.dedupe_service import find_dedupe_candidates

def run_dedupe():
    db = SessionLocal()
    leads = db.query(Lead).all()
    print(f"Loaded {len(leads)} leads from database for deduplication analysis.")
    print("Running two-stage blocking and candidate evaluation...")
    
    candidates = find_dedupe_candidates(leads, min_confidence=0.65)
    print(f"\nDiscovered {len(candidates)} suspected duplicate pairs (confidence >= 0.65):\n")
    
    for i, c in enumerate(candidates[:15], 1):
        print(f"[{i}] Confidence: {c.confidence_score*100:.0f}% ({c.confidence_level})")
        print(f"    Lead 1 (ID {c.lead_id_1}): {c.lead_1_name} | {c.lead_1_email} | {c.lead_1_company}")
        print(f"    Lead 2 (ID {c.lead_id_2}): {c.lead_2_name} | {c.lead_2_email} | {c.lead_2_company}")
        print(f"    Reason: {c.reason}")
        print(f"    Matched: {', '.join(c.matched_features)}")
        print("-" * 80)
        
    db.close()

if __name__ == "__main__":
    run_dedupe()
