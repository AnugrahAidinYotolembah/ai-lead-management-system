import csv
import io
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from app.models import Lead
from app.schemas import FormSubmissionIngest, LeadUpdate
from app.services.normalizer import (
    normalize_status,
    normalize_name,
    normalize_phone,
    normalize_email,
    normalize_date,
    clean_string,
)
from app.services.source_extractor import extract_source

def get_leads(
    db: Session,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    country: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Lead], int]:
    query = db.query(Lead)

    if status:
        query = query.filter(Lead.lead_status.ilike(f"%{status.strip()}%"))
    if owner:
        query = query.filter(Lead.contact_owner.ilike(f"%{owner.strip()}%"))
    if country:
        query = query.filter(Lead.country.ilike(f"%{country.strip()}%"))
    if q:
        q_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Lead.full_name.ilike(q_term),
                Lead.first_name.ilike(q_term),
                Lead.last_name.ilike(q_term),
                Lead.email.ilike(q_term),
                Lead.company_name.ilike(q_term),
            )
        )

    total = query.count()
    leads = query.order_by(desc(Lead.id)).offset(skip).limit(limit).all()
    return leads, total

def get_lead_by_id(db: Session, lead_id: int) -> Optional[Lead]:
    return db.query(Lead).filter(Lead.id == lead_id).first()

def update_lead(db: Session, lead_id: int, update_data: LeadUpdate) -> Optional[Lead]:
    lead = get_lead_by_id(db, lead_id)
    if not lead:
        return None

    if update_data.lead_status is not None:
        lead.lead_status = normalize_status(update_data.lead_status)
    if update_data.contact_owner is not None:
        lead.contact_owner = clean_string(update_data.contact_owner)
    if update_data.notes is not None:
        lead.notes = clean_string(update_data.notes)
        # Re-extract source channel if notes updated
        ext = extract_source(lead.notes or "", lead.original_source or "")
        lead.source_channel = ext["channel"]
        lead.source_detail = ext["detail"]

    lead.last_modified_date = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead

def export_leads_csv(
    db: Session,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    country: Optional[str] = None,
    q: Optional[str] = None,
) -> str:
    leads, _ = get_leads(db, status=status, owner=owner, country=country, q=q, skip=0, limit=10000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "ID", "Record ID", "First Name", "Last Name", "Full Name", "Job Title", 
        "Company Name", "Email", "Phone Number", "Country", "City", "Lead Status", 
        "Source Channel", "Source Detail", "Original Source", "Contact Owner", "Lead Score", "Notes"
    ]
    writer.writerow(headers)
    
    for lead in leads:
        writer.writerow([
            lead.id,
            lead.record_id or "",
            lead.first_name or "",
            lead.last_name or "",
            lead.full_name or "",
            lead.job_title or "",
            lead.company_name or "",
            lead.email or "",
            lead.phone_number or "",
            lead.country or "",
            lead.city or "",
            lead.lead_status or "",
            lead.source_channel or "",
            lead.source_detail or "",
            lead.original_source or "",
            lead.contact_owner or "",
            lead.lead_score or "",
            lead.notes or "",
        ])
        
    return output.getvalue()

def ingest_submission(db: Session, submission: FormSubmissionIngest) -> Tuple[Lead, str, Optional[str]]:
    """
    Accepts web form submission. Checks for existing lead by exact email or phone number.
    If exists: updates notes and contact information.
    If not: creates a new lead with AI extracted channel.
    """
    clean_email, local_p, domain = normalize_email(submission.email)
    display_phone, phone_norm = normalize_phone(submission.phone)
    first_name, last_name, full_name = normalize_name(None, None, submission.name)

    existing_lead = None
    matched_by = None

    # Check by email
    if clean_email:
        existing_lead = db.query(Lead).filter(Lead.email.ilike(clean_email)).first()
        if existing_lead:
            matched_by = "email"

    # If not found, check by phone
    if not existing_lead and phone_norm:
        existing_lead = db.query(Lead).filter(Lead.phone_normalized == phone_norm).first()
        if existing_lead:
            matched_by = "phone"

    new_note = clean_string(submission.message) or ""

    if existing_lead:
        # Update existing lead
        if submission.company and not existing_lead.company_name:
            existing_lead.company_name = submission.company
        if submission.country and not existing_lead.country:
            existing_lead.country = submission.country
        if display_phone and not existing_lead.phone_number:
            existing_lead.phone_number = display_phone
            existing_lead.phone_normalized = phone_norm
            
        if new_note:
            existing_lead.notes = new_note
                
            ext = extract_source(existing_lead.notes, existing_lead.original_source or "Website Form")
            existing_lead.source_channel = ext["channel"]
            existing_lead.source_detail = ext["detail"]

        existing_lead.last_modified_date = datetime.utcnow()
        db.commit()
        db.refresh(existing_lead)
        return existing_lead, "updated", matched_by
    else:
        # Create new lead
        ext = extract_source(new_note, "Website")
        created_at = normalize_date(submission.submitted_at) or datetime.utcnow()
        
        new_lead = Lead(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            company_name=clean_string(submission.company),
            email=clean_email,
            phone_number=display_phone,
            phone_normalized=phone_norm,
            country=clean_string(submission.country),
            lead_status="New",
            original_source="Website Form",
            source_channel=ext["channel"],
            source_detail=ext["detail"],
            notes=new_note,
            create_date=created_at,
            last_modified_date=datetime.utcnow()
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        return new_lead, "created", None

def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
    total_leads = db.query(Lead).count()

    # By status
    status_counts = (
        db.query(Lead.lead_status, func.count(Lead.id))
        .group_by(Lead.lead_status)
        .all()
    )
    by_status = {s or "Unknown": count for s, count in status_counts}

    # By channel
    channel_counts = (
        db.query(Lead.source_channel, func.count(Lead.id))
        .group_by(Lead.source_channel)
        .all()
    )
    by_channel = {c or "Unknown": count for c, count in channel_counts}

    # By Owner
    owner_counts = (
        db.query(Lead.contact_owner, func.count(Lead.id))
        .filter(Lead.contact_owner != None, Lead.contact_owner != "")
        .group_by(Lead.contact_owner)
        .order_by(desc(func.count(Lead.id)))
        .limit(6)
        .all()
    )
    by_owner = {o.strip(): count for o, count in owner_counts if o}

    # By Country
    country_counts = (
        db.query(Lead.country, func.count(Lead.id))
        .filter(Lead.country != None, Lead.country != "")
        .group_by(Lead.country)
        .order_by(desc(func.count(Lead.id)))
        .limit(6)
        .all()
    )
    by_country = {c.strip(): count for c, count in country_counts if c}

    return {
        "total_leads": total_leads,
        "by_status": by_status,
        "by_channel": by_channel,
        "by_owner": by_owner,
        "by_country": by_country,
    }
