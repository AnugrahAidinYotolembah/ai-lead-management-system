import pytest
from app.models import Lead
from app.services.dedupe_service import score_candidate_pair, find_dedupe_candidates
from app.services.normalizer import normalize_phone

def test_exact_duplicate_detection():
    l1 = Lead(
        id=101,
        first_name="Marcus",
        last_name="Russo",
        full_name="Marcus Russo",
        company_name="Diallo Imports Freight Solutions",
        email="marcus.russo@dialloimports.co",
        phone_normalized="46707792327"
    )
    l2 = Lead(
        id=102,
        first_name="M.",
        last_name="Russo",
        full_name="M. Russo",
        company_name="Diallo Imports Ltd",
        email="marcus.russo@dialloimports.co",
        phone_normalized="46707792327"
    )
    score, reason, features = score_candidate_pair(l1, l2)
    assert score >= 0.85
    assert "phone_match" in features
    assert "exact_email" in features

def test_different_people_same_company_not_overflagged():
    l1 = Lead(
        id=201,
        first_name="Alice",
        last_name="Zhang",
        full_name="Alice Zhang",
        company_name="Acme Global Corporation",
        email="alice.z@acmeglobal.com",
        phone_normalized="1234567890"
    )
    l2 = Lead(
        id=202,
        first_name="Bob",
        last_name="Johnson",
        full_name="Bob Johnson",
        company_name="Acme Global Corporation",
        email="bob.j@acmeglobal.com",
        phone_normalized="9876543210"
    )
    score, reason, features = score_candidate_pair(l1, l2)
    # Different names, different emails, different phones -> should be low score
    assert score < 0.50

def test_email_local_variation_match():
    l1 = Lead(
        id=301,
        first_name="Ines",
        last_name="Seo",
        full_name="Ines Seo",
        company_name="Patel Fintech and Co",
        email="iness@patelfintech.net",
        phone_normalized="821099887766"
    )
    l2 = Lead(
        id=302,
        first_name="Ines",
        last_name="Seo",
        full_name="Ines Seo",
        company_name="Patel Fintech Group",
        email="ines.seo@patelfintech.net",
        phone_normalized="821099887766"
    )
    score, reason, features = score_candidate_pair(l1, l2)
    assert score >= 0.85
    assert "same_email_domain" in features
