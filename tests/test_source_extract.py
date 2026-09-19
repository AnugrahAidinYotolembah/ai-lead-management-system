import pytest
from app.services.source_extractor import extract_source

def test_extract_event_booth_qr():
    note = "He scanned our QR code at the SaaStr Annual booth. Great fit, prioritizing."
    result = extract_source(note)
    assert result["channel"] == "Event"
    assert "SaaStr" in result["detail"] or "Booth" in result["detail"]

def test_extract_referral_with_name():
    note = "Referred by Michael Zhang, warm intro. Connected, sending proposal."
    result = extract_source(note)
    assert result["channel"] == "Referral"
    assert "Michael Zhang" in result["detail"]

def test_extract_organic_search():
    note = "Googled us and ended up on the book-a-demo page before booking a demo."
    result = extract_source(note)
    assert result["channel"] == "Organic Search"

def test_extract_linkedin_engagement():
    note = "Connected on LinkedIn after commenting on our post. Connected, sending proposal."
    result = extract_source(note)
    assert result["channel"] == "LinkedIn"

def test_extract_manual_cold_call():
    note = "Manually added by sales after a phone call from a cold outreach list."
    result = extract_source(note)
    assert result["channel"] == "Manual/Sales"

def test_fallback_other():
    note = "Random conversation with unknown party about generic logistics."
    result = extract_source(note)
    assert result["channel"] in ["Other", "Manual/Sales"]
