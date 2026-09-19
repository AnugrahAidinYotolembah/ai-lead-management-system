import os
import re
import json
from typing import Dict, Any, Tuple
from app.config import (
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    LLM_PROVIDER,
    LLM_MODEL,
    STANDARD_CHANNELS
)

def extract_source_heuristic(notes: str, original_source: str = "") -> Tuple[str, str]:
    text = (notes or "") + " " + (original_source or "")
    text_lower = text.lower()
    
    # 1. Event
    event_keywords = [
        "booth", "qr code", "conference", "summit", "festival", "expo", "disrupt", 
        "saastr", "mobile world congress", "mwc", "fintech", "sff", "ces", "web summit"
    ]
    if any(kw in text_lower for kw in event_keywords):
        detail = "Event"
        if "saastr" in text_lower:
            detail = "SaaStr Annual — Booth QR Code"
        elif "techcrunch" in text_lower or "disrupt" in text_lower:
            detail = "TechCrunch Disrupt — Booth QR Code"
        elif "mobile world congress" in text_lower or "mwc" in text_lower:
            detail = "Mobile World Congress (MWC) — Booth"
        elif "fintech" in text_lower or "sff" in text_lower:
            detail = "Singapore FinTech Festival — Booth QR Code"
        elif "qr code" in text_lower or "booth" in text_lower:
            detail = "Industry Conference/Expo — Booth QR Code"
        return "Event", detail

    # 2. LinkedIn
    if "linkedin" in text_lower or "linked in" in text_lower:
        detail = "LinkedIn connection / post engagement"
        if "comment" in text_lower:
            detail = "LinkedIn — Inbound comment on post"
        elif "inmail" in text_lower or "message" in text_lower:
            detail = "LinkedIn — InMail / Direct Message"
        return "LinkedIn", detail

    # 3. Referral
    if "referr" in text_lower or "warm intro" in text_lower or "introduced by" in text_lower:
        match = re.search(r"referred by ([^,.\n]+)", text, re.IGNORECASE)
        if match:
            detail = f"Referred by {match.group(1).strip()}"
        else:
            detail = "Customer/Partner Warm Referral"
        return "Referral", detail

    # 4. Organic Search
    if "google" in text_lower or "organic search" in text_lower or "googled us" in text_lower or "search engine" in text_lower:
        detail = "Organic Google Search"
        if "book-a-demo" in text_lower or "demo" in text_lower:
            detail += " — Demo Request"
        elif "product tour" in text_lower:
            detail += " — Product Tour Page"
        return "Organic Search", detail

    # 5. Website
    if any(k in text_lower for k in ["form on", "contact page", "newsletter", "pricing page", "blog post", "book-a-demo", "website"]):
        detail = "Website Form Submission"
        if "pricing" in text_lower:
            detail = "Website — Pricing Page Form"
        elif "blog" in text_lower:
            detail = "Website — Blog Post Form"
        elif "contact" in text_lower:
            detail = "Website — Contact Page Form"
        elif "demo" in text_lower:
            detail = "Website — Demo Request Page"
        return "Website", detail

    # 6. Manual / Sales
    if any(k in text_lower for k in ["manually added", "cold outreach", "phone call", "cold list", "sales outbound", "walked into", "inbound phone"]):
        detail = "Manual Sales Outreach / Inbound Call"
        if "walked into" in text_lower:
            detail = "Walk-in Visitor"
        elif "cold outreach" in text_lower or "cold list" in text_lower:
            detail = "Cold Sales Outreach List"
        elif "inbound phone" in text_lower:
            detail = "Inbound Phone Call"
        return "Manual/Sales", detail

    # Fallback to Original Source if present
    if original_source:
        orig_lower = original_source.lower()
        if "referral" in orig_lower:
            return "Referral", original_source
        if "organic" in orig_lower:
            return "Organic Search", original_source
        if "direct" in orig_lower or "website" in orig_lower:
            return "Website", original_source
        if "event" in orig_lower:
            return "Event", original_source

    return "Other", text[:100].strip() or "General inquiry"

def extract_source_llm(notes: str, original_source: str = "") -> Tuple[str, str]:
    """
    Attempt extraction using OpenRouter, OpenAI, or Gemini if API key is provided,
    otherwise fallback cleanly to heuristic extractor.
    """
    prompt = (
        f"You are a CRM AI. Extract structured lead source from this note.\n"
        f"Valid channels: {json.dumps(STANDARD_CHANNELS)}\n\n"
        f"Notes: {notes}\n"
        f"Original Source: {original_source}\n\n"
        f"Respond ONLY with a valid JSON object without markdown fences: {{\"channel\": \"<one of valid channels>\", \"detail\": \"<brief detail>\"}}"
    )

    # 1. OpenRouter
    if OPENROUTER_API_KEY and (LLM_PROVIDER in ["openrouter", "auto"]):
        try:
            import requests
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://127.0.0.1:8000",
                    "X-Title": "Wiz CRM Lead Management",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                timeout=12
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_content = data["choices"][0]["message"]["content"].strip()
                # Clean up any potential markdown backticks from LLM output
                raw_json = re.sub(r"^```json\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
                # Find JSON curly brackets
                json_match = re.search(r"\{.*\}", raw_json, re.DOTALL)
                if json_match:
                    res = json.loads(json_match.group(0))
                    channel = res.get("channel", "Other")
                    if channel not in STANDARD_CHANNELS:
                        channel = "Other"
                    detail = res.get("detail", notes[:60])
                    return channel, detail
        except Exception:
            pass

    # 2. OpenAI
    if OPENAI_API_KEY and (LLM_PROVIDER in ["openai", "auto"]):
        try:
            import requests
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"}
                },
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                res = json.loads(content)
                channel = res.get("channel", "Other")
                if channel not in STANDARD_CHANNELS:
                    channel = "Other"
                detail = res.get("detail", notes[:60])
                return channel, detail
        except Exception:
            pass

    # Fallback to local heuristic extractor
    return extract_source_heuristic(notes, original_source)

def extract_source(notes: str, original_source: str = "") -> Dict[str, str]:
    if OPENROUTER_API_KEY or OPENAI_API_KEY or GEMINI_API_KEY:
        channel, detail = extract_source_llm(notes, original_source)
        provider_name = "openrouter" if OPENROUTER_API_KEY else "llm"
        method = f"{provider_name} ({OPENROUTER_MODEL if OPENROUTER_API_KEY else 'openai'})"
    else:
        channel, detail = extract_source_heuristic(notes, original_source)
        method = "heuristic_rule_engine"
        
    return {
        "channel": channel,
        "detail": detail,
        "method": method
    }
