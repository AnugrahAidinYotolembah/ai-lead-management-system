import re
from difflib import SequenceMatcher
from collections import defaultdict
from typing import List, Dict, Any, Tuple
from app.models import Lead
from app.schemas import DedupeCandidateItem

def string_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    cleaned = name.lower()
    # Remove common legal suffixes and noise
    for suffix in [
        "pte ltd", "pte. ltd.", "ltd", "ltd.", "inc", "inc.", "co", "co.", 
        "corp", "corp.", "and co", "& co", "trading", "partners", "solutions", 
        "freight", "logistics", "consulting", "ab"
    ]:
        cleaned = re.sub(rf"\b{re.escape(suffix)}\b", "", cleaned)
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()

def extract_email_tokens(email: str) -> Tuple[str, str]:
    if not email or "@" not in email:
        return "", ""
    parts = email.lower().strip().split("@", 1)
    local = parts[0]
    domain = parts[1]
    # Strip dots/hyphens from localpart (e.g. j.doe vs jdoe)
    clean_local = re.sub(r"[.\-_]", "", local)
    return clean_local, domain

def generate_blocks(leads: List[Lead]) -> Dict[str, List[Lead]]:
    """
    Candidate Generation / Blocking Phase (O(N)):
    Generates blocking keys so we only compare candidate pairs within the same bucket.
    This avoids 2,000 * 2,000 = 4,000,000 comparisons!
    """
    blocks = defaultdict(list)
    
    for lead in leads:
        # 1. Block by normalized phone (last 7-9 digits)
        if lead.phone_normalized and len(lead.phone_normalized) >= 7:
            phone_key = f"phone:{lead.phone_normalized[-7:]}"
            blocks[phone_key].append(lead)

        # 2. Block by email domain + first letter of first name
        clean_local, domain = extract_email_tokens(lead.email)
        first_letter = (lead.first_name or "")[:1].lower()
        if domain and first_letter:
            blocks[f"domain_first:{domain}:{first_letter}"].append(lead)

        # 3. Block by clean local-part of email (handles same user across domain variations or subdomains)
        if clean_local and len(clean_local) >= 4:
            blocks[f"email_local:{clean_local}"].append(lead)

        # 4. Block by normalized company + first letter of last name
        clean_comp = normalize_company_name(lead.company_name or "")
        last_letter = (lead.last_name or "")[:1].lower()
        if len(clean_comp) >= 3 and last_letter:
            blocks[f"comp_last:{clean_comp[:8]}:{last_letter}"].append(lead)
            
    return blocks

def score_candidate_pair(l1: Lead, l2: Lead) -> Tuple[float, str, List[str]]:
    """
    Evaluates two candidate leads using a multi-feature similarity model:
    - Name similarity (Full name & First/Last)
    - Email similarity & domain match
    - Phone number match
    - Company name similarity
    """
    score = 0.0
    matched_features = []
    reasons = []

    # 1. Phone match
    phone_matched = False
    if l1.phone_normalized and l2.phone_normalized:
        if l1.phone_normalized == l2.phone_normalized or l1.phone_normalized[-7:] == l2.phone_normalized[-7:]:
            score += 0.40
            phone_matched = True
            matched_features.append("phone_match")
            reasons.append("Identical normalized phone number digits")

    # 2. Email comparison
    email_local1, domain1 = extract_email_tokens(l1.email)
    email_local2, domain2 = extract_email_tokens(l2.email)
    
    email_sim = string_similarity(l1.email, l2.email)
    if l1.email and l2.email and l1.email.lower() == l2.email.lower():
        score += 0.50
        matched_features.append("exact_email")
        reasons.append("Exact email match")
    elif domain1 and domain2 and domain1 == domain2:
        matched_features.append("same_email_domain")
        local_sim = string_similarity(email_local1, email_local2)
        if local_sim > 0.8:
            score += 0.35
            matched_features.append("high_email_local_similarity")
            reasons.append(f"Matching email domain '{domain1}' with similar handle ({email_local1} vs {email_local2})")
        else:
            score += 0.10
    elif email_sim > 0.85:
        score += 0.30
        matched_features.append("similar_email")
        reasons.append(f"High email string similarity ({int(email_sim*100)}%)")

    # 3. Name comparison
    name1 = (l1.full_name or f"{l1.first_name or ''} {l1.last_name or ''}").strip()
    name2 = (l2.full_name or f"{l2.first_name or ''} {l2.last_name or ''}").strip()
    name_sim = string_similarity(name1, name2)
    
    if name_sim >= 0.92:
        score += 0.30
        matched_features.append("exact_or_near_name")
        reasons.append(f"Names match closely ('{name1}' vs '{name2}')")
    elif name_sim >= 0.75:
        score += 0.20
        matched_features.append("similar_name")
        reasons.append(f"Name similarity ({int(name_sim*100)}%)")
    elif name_sim < 0.4 and not phone_matched:
        # Penalty if names are completely different and no strong phone match
        score -= 0.25

    # 4. Company comparison
    comp1 = normalize_company_name(l1.company_name or "")
    comp2 = normalize_company_name(l2.company_name or "")
    comp_sim = string_similarity(comp1, comp2)
    
    if comp1 and comp2 and (comp1 == comp2 or comp_sim >= 0.85):
        score += 0.15
        matched_features.append("company_match")
        reasons.append(f"Identical or similar company ('{l1.company_name}' vs '{l2.company_name}')")

    # Bound score between 0.0 and 1.0
    final_score = max(0.0, min(1.0, round(score, 2)))
    reason_str = "; ".join(reasons) if reasons else "Partial attribute overlap"
    return final_score, reason_str, matched_features

def find_dedupe_candidates(leads: List[Lead], min_confidence: float = 0.65) -> List[DedupeCandidateItem]:
    """
    Scalable deduplication engine:
    1. Blocks ~2,000 leads into high-probability buckets
    2. Runs pairwise scoring only within candidate blocks
    3. Returns sorted list of likely duplicate pairs
    """
    blocks = generate_blocks(leads)
    seen_pairs = set()
    candidate_items: List[DedupeCandidateItem] = []

    for block_key, block_leads in blocks.items():
        n = len(block_leads)
        if n < 2 or n > 150: # Avoid super-blocks (e.g. empty fields)
            continue
            
        for i in range(n):
            for j in range(i + 1, n):
                l1 = block_leads[i]
                l2 = block_leads[j]
                
                pair_key = (min(l1.id, l2.id), max(l1.id, l2.id))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                
                conf_score, reason, features = score_candidate_pair(l1, l2)
                
                if conf_score >= min_confidence:
                    if conf_score >= 0.85:
                        level = "HIGH"
                    elif conf_score >= 0.70:
                        level = "MEDIUM"
                    else:
                        level = "LOW"

                    candidate_items.append(
                        DedupeCandidateItem(
                            lead_id_1=l1.id,
                            lead_1_name=l1.full_name or f"{l1.first_name} {l1.last_name}",
                            lead_1_email=l1.email,
                            lead_1_company=l1.company_name,
                            lead_id_2=l2.id,
                            lead_2_name=l2.full_name or f"{l2.first_name} {l2.last_name}",
                            lead_2_email=l2.email,
                            lead_2_company=l2.company_name,
                            confidence_score=conf_score,
                            confidence_level=level,
                            reason=reason,
                            matched_features=features
                        )
                    )

    # Sort descending by confidence score
    candidate_items.sort(key=lambda x: x.confidence_score, reverse=True)
    return candidate_items
