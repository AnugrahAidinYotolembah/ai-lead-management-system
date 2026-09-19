import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Lead

client = TestClient(app)

def test_list_leads():
    response = client.get("/leads?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_filter_leads_by_status():
    response = client.get("/leads?status=Qualified")
    assert response.status_code == 200
    data = response.json()
    for lead in data:
        assert "qual" in lead["lead_status"].lower()

def test_search_leads():
    response = client.get("/leads?q=gmail")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_single_lead():
    # Fetch first lead ID
    leads_resp = client.get("/leads?limit=1")
    first_lead = leads_resp.json()[0]
    lead_id = first_lead["id"]

    response = client.get(f"/leads/{lead_id}")
    assert response.status_code == 200
    assert response.json()["id"] == lead_id

def test_patch_lead():
    leads_resp = client.get("/leads?limit=1")
    lead_id = leads_resp.json()[0]["id"]

    update_payload = {
        "lead_status": "Closed Won",
        "contact_owner": "Test Automation Owner",
        "notes": "Met at Singapore FinTech Festival booth, scanned QR code"
    }
    response = client.patch(f"/leads/{lead_id}", json=update_payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["lead_status"] == "Closed Won"
    assert updated["contact_owner"] == "Test Automation Owner"
    # Verification that note change triggers source re-extraction
    assert updated["source_channel"] == "Event"

def test_export_leads_csv():
    response = client.get("/leads/export?limit=5")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "First Name" in response.text

def test_ingest_new_lead_and_update_existing():
    import uuid
    rand_email = f"alex.{uuid.uuid4().hex[:8]}@testauthor.com"
    rand_phone = f"+33 6 {uuid.uuid4().hex[:8]}"

    # 1. Ingest new
    new_submission = {
        "name": "Alexandre Dumas",
        "email": rand_email,
        "phone": rand_phone,
        "company": "Musketeers Media",
        "country": "France",
        "message": "Interested in enterprise CRM."
    }
    resp1 = client.post("/leads/ingest", json=new_submission)
    assert resp1.status_code == 200
    res1 = resp1.json()
    assert res1["status"] == "created"
    lead_id = res1["lead"]["id"]

    # 2. Ingest duplicate email (should update)
    update_submission = {
        "name": "Alex Dumas",
        "email": rand_email,
        "phone": rand_phone,
        "message": "Following up with additional requirements."
    }
    resp2 = client.post("/leads/ingest", json=update_submission)
    assert resp2.status_code == 200
    res2 = resp2.json()
    assert res2["status"] == "updated"
    assert res2["lead"]["id"] == lead_id
    assert res2["matched_by"] == "email"

def test_dashboard_endpoint():
    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_leads" in data
    assert "by_status" in data
    assert "by_channel" in data
    assert data["total_leads"] > 0
