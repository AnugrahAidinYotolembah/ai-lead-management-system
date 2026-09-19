import os
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app.models import Lead
from app.schemas import (
    LeadResponse,
    LeadUpdate,
    FormSubmissionIngest,
    IngestResponse,
    DedupeResponse,
    SourceExtractRequest,
    SourceExtractResponse,
    DashboardSummary,
)
from app.services.lead_service import (
    get_leads,
    get_lead_by_id,
    update_lead,
    export_leads_csv,
    ingest_submission,
    get_dashboard_metrics,
)
from app.services.dedupe_service import find_dedupe_candidates
from app.services.source_extractor import extract_source

# Ensure DB schema created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Assisted Mini Lead Management System",
    description="Streamlined HubSpot replacement prototype with AI deduplication & source extraction",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & Templates setup
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# UI Dashboard Route
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard-ui", response_class=HTMLResponse)
def serve_dashboard_ui(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# 1. Lead store API
@app.get("/leads", response_model=List[LeadResponse])
def list_leads(
    status: Optional[str] = Query(None, description="Filter by lead status (e.g., 'New', 'Qualified')"),
    owner: Optional[str] = Query(None, description="Filter by Contact Owner"),
    country: Optional[str] = Query(None, description="Filter by Country/Region"),
    q: Optional[str] = Query(None, description="Free-text search across name, company, email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    leads, _ = get_leads(db, status=status, owner=owner, country=country, q=q, skip=skip, limit=limit)
    return leads

@app.get("/leads/export")
def export_filtered_leads(
    status: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    csv_content = export_leads_csv(db, status=status, owner=owner, country=country, q=q)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=filtered_leads_export.csv"}
    )

@app.get("/leads/{lead_id}", response_model=LeadResponse)
def get_single_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.patch("/leads/{lead_id}", response_model=LeadResponse)
def patch_lead(lead_id: int, update_data: LeadUpdate, db: Session = Depends(get_db)):
    lead = update_lead(db, lead_id, update_data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.post("/leads/ingest", response_model=IngestResponse)
def ingest_form_lead(submission: FormSubmissionIngest, db: Session = Depends(get_db)):
    lead, action, matched_by = ingest_submission(db, submission)
    return IngestResponse(
        status=action,
        lead=LeadResponse.model_validate(lead),
        matched_by=matched_by
    )

# 2. AI-Assisted Deduplication
@app.post("/leads/dedupe-candidates", response_model=DedupeResponse)
def dedupe_candidates(
    min_confidence: float = Query(0.65, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    leads = db.query(Lead).all()
    candidates = find_dedupe_candidates(leads, min_confidence=min_confidence)
    return DedupeResponse(
        total_candidates=len(candidates),
        groups=candidates
    )

# 3. AI-Assisted Source Extraction
@app.post("/leads/extract-source", response_model=SourceExtractResponse)
def extract_lead_source(req: SourceExtractRequest):
    result = extract_source(req.notes, req.original_source or "")
    return SourceExtractResponse(
        channel=result["channel"],
        detail=result["detail"],
        method=result["method"]
    )

# 4. Dashboard Metrics Endpoint
@app.get("/dashboard", response_model=DashboardSummary)
def dashboard_metrics(db: Session = Depends(get_db)):
    metrics = get_dashboard_metrics(db)
    return DashboardSummary(
        total_leads=metrics["total_leads"],
        by_status=metrics["by_status"],
        by_channel=metrics["by_channel"],
        by_owner=metrics["by_owner"],
        by_country=metrics["by_country"],
    )
