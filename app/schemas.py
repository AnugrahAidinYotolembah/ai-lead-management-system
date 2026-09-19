from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LeadBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    lead_status: Optional[str] = "New"
    lifecycle_stage: Optional[str] = None
    original_source: Optional[str] = None
    source_channel: Optional[str] = None
    source_detail: Optional[str] = None
    contact_owner: Optional[str] = None
    lead_score: Optional[float] = None
    notes: Optional[str] = None

class LeadResponse(LeadBase):
    id: int
    record_id: Optional[str] = None
    phone_normalized: Optional[str] = None
    create_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None

    model_config = {"from_attributes": True}

class LeadUpdate(BaseModel):
    lead_status: Optional[str] = None
    contact_owner: Optional[str] = None
    notes: Optional[str] = None

class FormSubmissionIngest(BaseModel):
    form_id: Optional[str] = None
    form_name: Optional[str] = None
    page_url: Optional[str] = None
    submitted_at: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    country: Optional[str] = None
    message: Optional[str] = None

class IngestResponse(BaseModel):
    status: str # "created" or "updated"
    lead: LeadResponse
    matched_by: Optional[str] = None # "email" or "phone"

class DedupeCandidateItem(BaseModel):
    lead_id_1: int
    lead_1_name: Optional[str] = None
    lead_1_email: Optional[str] = None
    lead_1_company: Optional[str] = None
    
    lead_id_2: int
    lead_2_name: Optional[str] = None
    lead_2_email: Optional[str] = None
    lead_2_company: Optional[str] = None
    
    confidence_score: float
    confidence_level: str # HIGH, MEDIUM, LOW
    reason: str
    matched_features: List[str]

class DedupeResponse(BaseModel):
    total_candidates: int
    groups: List[DedupeCandidateItem]

class SourceExtractRequest(BaseModel):
    notes: str
    original_source: Optional[str] = None

class SourceExtractResponse(BaseModel):
    channel: str
    detail: str
    method: str # "llm" or "heuristic_fallback"

class DashboardSummary(BaseModel):
    total_leads: int
    by_status: Dict[str, int]
    by_channel: Dict[str, int]
    by_owner: Dict[str, int]
    by_country: Dict[str, int]
