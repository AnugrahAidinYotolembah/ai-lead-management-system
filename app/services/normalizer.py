import re
from datetime import datetime
from typing import Tuple, Optional

# Status normalization map
STATUS_MAP = {
    "new": "New",
    "qualified": "Qualified",
    "contacted": "Contacted",
    "connected": "Connected",
    "opportunity": "Opportunity",
    "closed won": "Closed Won",
    "closed lost": "Closed Lost",
}

def clean_string(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None

def normalize_status(val: Optional[str]) -> str:
    cleaned = clean_string(val)
    if not cleaned:
        return "New"
    
    cleaned_lower = cleaned.lower()
    # Direct or partial match
    for key, std in STATUS_MAP.items():
        if cleaned_lower == key or key in cleaned_lower:
            return std
    return cleaned.capitalize()

def normalize_phone(val: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (cleaned_display_phone, digits_only_phone)
    """
    cleaned = clean_string(val)
    if not cleaned:
        return None, None
    digits = re.sub(r"\D", "", cleaned)
    return cleaned, digits if len(digits) >= 6 else None

def normalize_name(first: Optional[str], last: Optional[str], full: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    first = clean_string(first)
    last = clean_string(last)
    full = clean_string(full)

    if full and (not first or not last):
        parts = full.split()
        if len(parts) == 1:
            first = parts[0]
            last = ""
        elif len(parts) > 1:
            first = parts[0]
            last = " ".join(parts[1:])
    elif first or last:
        parts = [p for p in [first, last] if p]
        full = " ".join(parts)
        
    return first, last, full

def normalize_date(val: Optional[str]) -> Optional[datetime]:
    s = clean_string(val)
    if not s:
        return None
        
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m/%d/%y",
        "%Y/%m/%d",
    ]
    
    # Try ISO or standard formats
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
            
    # If date contains T but timezone offset like +00:00 or milliseconds
    try:
        clean_iso = re.sub(r"\.\d+", "", s)
        clean_iso = clean_iso.replace("Z", "")
        if "T" in clean_iso:
            return datetime.fromisoformat(clean_iso)
    except Exception:
        pass

    return None

def normalize_email(val: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns (cleaned_email, local_part, domain)
    """
    s = clean_string(val)
    if not s or "@" not in s:
        return s, None, None
    
    email_lower = s.lower()
    parts = email_lower.split("@", 1)
    local_part = parts[0].strip()
    domain = parts[1].strip()
    return email_lower, local_part, domain
