import os
import sys
import csv
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, SessionLocal, Base
from app.models import Lead
from app.services.normalizer import (
    normalize_status,
    normalize_name,
    normalize_phone,
    normalize_email,
    normalize_date,
    clean_string,
)
from app.services.source_extractor import extract_source
from app.config import SEED_CSV_PATH

def import_csv():
    print(f"Checking database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    existing_count = db.query(Lead).count()
    if existing_count > 0:
        print(f"Database already contains {existing_count} leads. Cleaning existing table for fresh seed import...")
        db.query(Lead).delete()
        db.commit()

    if not os.path.exists(SEED_CSV_PATH):
        print(f"Error: Seed file not found at {SEED_CSV_PATH}")
        return

    print(f"Reading and normalizing seed data from {SEED_CSV_PATH}...")
    
    leads_to_insert = []
    with open(SEED_CSV_PATH, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        row_idx = 0
        for row in reader:
            row_idx += 1
            record_id = clean_string(row.get("Record ID"))
            raw_first = row.get("First Name")
            raw_last = row.get("Last Name")
            raw_full = row.get("Full Name")
            
            first_name, last_name, full_name = normalize_name(raw_first, raw_last, raw_full)
            job_title = clean_string(row.get("Job Title"))
            company_name = clean_string(row.get("Company Name"))
            
            clean_email, _, _ = normalize_email(row.get("Email"))
            display_phone, phone_norm = normalize_phone(row.get("Phone Number"))
            
            country = clean_string(row.get("Country/Region"))
            city = clean_string(row.get("City"))
            
            status = normalize_status(row.get("Lead Status"))
            lifecycle_stage = clean_string(row.get("Lifecycle Stage"))
            
            original_source = clean_string(row.get("Original Source"))
            drilldown1 = clean_string(row.get("Original Source Drill-Down 1"))
            contact_owner = clean_string(row.get("Contact Owner"))
            
            # Score
            raw_score = clean_string(row.get("Lead Score"))
            lead_score = None
            if raw_score:
                try:
                    lead_score = float(raw_score)
                except ValueError:
                    lead_score = None
                    
            notes = clean_string(row.get("Notes"))
            create_date = normalize_date(row.get("Create Date"))
            modified_date = normalize_date(row.get("Last Modified Date"))
            
            # AI Extract Channel from messy notes
            source_info = extract_source(notes or "", original_source or "")
            
            lead = Lead(
                record_id=record_id,
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                job_title=job_title,
                company_name=company_name,
                email=clean_email,
                phone_number=display_phone,
                phone_normalized=phone_norm,
                country=country,
                city=city,
                lead_status=status,
                lifecycle_stage=lifecycle_stage,
                original_source=original_source,
                original_source_drilldown1=drilldown1,
                source_channel=source_info["channel"],
                source_detail=source_info["detail"],
                contact_owner=contact_owner,
                lead_score=lead_score,
                notes=notes,
                create_date=create_date,
                last_modified_date=modified_date or create_date,
            )
            leads_to_insert.append(lead)
            
            if len(leads_to_insert) >= 500:
                db.bulk_save_objects(leads_to_insert)
                db.commit()
                leads_to_insert = []
                print(f"Processed {row_idx} leads...")

    if leads_to_insert:
        db.bulk_save_objects(leads_to_insert)
        db.commit()

    total = db.query(Lead).count()
    print(f"Successfully imported and normalized {total} leads into SQLite!")
    db.close()

if __name__ == "__main__":
    import_csv()
