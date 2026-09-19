from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from app.database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    record_id = Column(String(64), unique=True, index=True, nullable=True) # Original CRM ID if any
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    full_name = Column(String(256), index=True, nullable=True)
    job_title = Column(String(128), nullable=True)
    company_name = Column(String(256), index=True, nullable=True)
    email = Column(String(256), index=True, nullable=True)
    phone_number = Column(String(64), nullable=True)
    phone_normalized = Column(String(32), index=True, nullable=True) # digits only for dedup blocking
    country = Column(String(128), index=True, nullable=True)
    city = Column(String(128), nullable=True)
    
    lead_status = Column(String(64), index=True, default="New")
    lifecycle_stage = Column(String(64), nullable=True)
    
    original_source = Column(String(128), nullable=True)
    original_source_drilldown1 = Column(String(256), nullable=True)
    source_channel = Column(String(64), index=True, nullable=True) # AI extracted
    source_detail = Column(String(256), nullable=True)            # AI extracted
    
    contact_owner = Column(String(128), index=True, nullable=True)
    lead_score = Column(Float, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    create_date = Column(DateTime, default=datetime.utcnow, nullable=True)
    last_modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "record_id": self.record_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "phone_normalized": self.phone_normalized,
            "country": self.country,
            "city": self.city,
            "lead_status": self.lead_status,
            "lifecycle_stage": self.lifecycle_stage,
            "original_source": self.original_source,
            "source_channel": self.source_channel,
            "source_detail": self.source_detail,
            "contact_owner": self.contact_owner,
            "lead_score": self.lead_score,
            "notes": self.notes,
            "create_date": self.create_date.isoformat() if self.create_date else None,
            "last_modified_date": self.last_modified_date.isoformat() if self.last_modified_date else None,
        }
