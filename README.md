# AI-Assisted Mini Lead Management System

WIZ.AI Take-Home Assignment for AI Builder (Mid-Level) — An AI-assisted mini CRM system with scalable deduplication, NLP source extraction, and interactive dashboard built with FastAPI.

A lightweight, production-oriented CRM prototype built with **Python, FastAPI, SQLite, and AI/LLM-assisted workflows**.

The system is designed to handle messy, real-world CRM data, including inconsistent names, mixed date formats, phone number variations, unstructured sales notes, and duplicate contacts.

---

## 👤 Candidate Information

| Information           | Details                                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| **Name**              | Anugrah Aidin Yotolembah                                                                                 |
| **Role**              | Candidate for AI Builder (Mid-Level)                                                                     |
| **Email**             | [didiyotolembah19@gmail.com](mailto:didiyotolembah19@gmail.com)                                          |
| **LinkedIn**          | [linkedin.com/in/anugrahaidinyotolembah191201](https://www.linkedin.com/in/anugrahaidinyotolembah191201) |
| **Assignment Status** | 100% Core & Bonus Requirements Completed                                                                 |

---

## 🛠️ Technology Stack & Architectural Decisions

| Layer / Component        | Technology                                  | Rationale & Engineering Decision                                                                                                                   |
| ------------------------ | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Backend Framework**    | **FastAPI (Python 3.10+)**                  | High-performance ASGI framework with asynchronous support, automatic OpenAPI/Swagger documentation, and native type validation.                    |
| **Data Validation**      | **Pydantic v2**                             | Provides high-performance data parsing, request/response validation, and strongly typed data contracts.                                            |
| **Database & ORM**       | **SQLite + SQLAlchemy 2.0**                 | Zero-configuration, single-file relational database for local execution, with an ORM architecture that can transition to PostgreSQL in production. |
| **AI / LLM Integration** | **OpenRouter API — LLaMA 3.3 70B**          | Provides LLM-based extraction for unstructured sales notes, with support for configurable AI providers.                                            |
| **Fallback AI Engine**   | **Deterministic Regex Rule Engine**         | Provides a local fallback when the LLM service is unavailable, allowing the extraction workflow to continue without network access.                |
| **Frontend / Dashboard** | **HTML5 + Modern CSS + Vanilla JavaScript** | Lightweight responsive dashboard with a glassmorphic dark-mode design, served directly by FastAPI without heavy Node.js/NPM build dependencies.    |
| **Testing**              | **Pytest + TestClient (HTTPX)**             | Automated unit and integration testing covering CRUD operations, deduplication, filtering, ingestion, and source extraction.                       |

---

## 📂 Project Structure

```text
lead_management_system/
│
├── app/
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   ├── services/
│   │   ├── normalizer.py
│   │   ├── dedupe_service.py
│   │   ├── source_extractor.py
│   │   └── lead_service.py
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   │
│   ├── templates/
│   │   └── index.html
│   │
│   └── main.py
│
├── data/
│   ├── leads_seed.csv
│   └── website_form_submissions.json
│
├── scripts/
│   ├── import_seed.py
│   └── run_dedupe.py
│
├── tests/
│   ├── test_leads_api.py
│   ├── test_dedupe.py
│   └── test_source_extract.py
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📋 File Responsibilities

### `app/config.py`

Application configuration and environment management.

* Loads environment variables using `python-dotenv`.
* Defines canonical CRM statuses:

  * `New`
  * `Qualified`
  * `Connected`
  * `Contacted`
  * `Opportunity`
  * `Closed Won`
  * `Closed Lost`
* Defines supported marketing channels.
* Configures the OpenRouter API, selected model, and database path.

### `app/database.py`

Database initialization and session management.

* Configures the SQLAlchemy engine.
* Handles SQLite thread-safety configuration.
* Provides the `get_db()` dependency for FastAPI endpoints.
* Manages database session lifecycle and cleanup.

### `app/models.py`

Defines the SQLAlchemy ORM model for the `Lead` entity.

In addition to standard CRM fields, it contains specialized fields such as:

* `phone_normalized` — digit-only phone representation used for indexing and deduplication.
* `source_channel` — normalized marketing source channel.
* `source_detail` — detailed attribution extracted from sales notes.

### `app/schemas.py`

Contains Pydantic schemas used for request and response validation.

Key schemas include:

* `LeadResponse`
* `LeadUpdate`
* `FormSubmissionIngest`
* `DedupeResponse`
* `DedupeCandidateItem`
* `SourceExtractRequest`
* `SourceExtractResponse`
* `DashboardSummary`

### `app/services/normalizer.py`

Core data-normalization module for processing messy CRM records.

It provides:

* `normalize_name()` — combines or reconciles split first/last names and full names.
* `normalize_status()` — converts inconsistent casing and whitespace into canonical CRM statuses.
* `normalize_phone()` — removes formatting and converts phone numbers into clean digit-based values.
* `normalize_date()` — handles multiple date formats, including `YYYY-MM-DD`, `M/D/YYYY`, and ISO 8601 timestamps.

### `app/services/dedupe_service.py`

Implements the scalable two-stage deduplication process.

The system:

1. Creates inverted blocking keys to reduce unnecessary comparisons.
2. Generates candidate pairs within relevant blocks.
3. Scores candidates using multiple attributes.
4. Produces confidence scores and match levels.

The scoring considers:

* Name similarity
* Email local-part similarity
* Email domain
* Phone number equality
* Company-name similarity
* Company legal suffix normalization

### `app/services/source_extractor.py`

Implements the hybrid NLP source-extraction pipeline.

The service:

1. Sends unstructured sales notes to the configured LLM.
2. Converts the response into a structured JSON format.
3. Falls back to a local regex-based rule engine when the LLM is unavailable.

Example output:

```json
{
  "channel": "Event",
  "detail": "Singapore FinTech Festival — Booth QR Code"
}
```

### `app/services/lead_service.py`

Contains the main business logic for lead management.

Responsibilities include:

* Paginated lead listing.
* Multi-attribute filtering.
* Free-text search using `q`.
* Lead updates through `PATCH`.
* Automatic source re-extraction when notes are modified.
* Dynamic CSV export based on active filters.
* Webhook ingestion.
* Duplicate checking during ingestion.
* Dashboard KPI aggregation.

### `app/main.py`

FastAPI application entry point.

Responsibilities include:

* FastAPI initialization.
* CORS configuration.
* Static file mounting.
* Jinja2 template configuration.
* REST API routing.
* Dashboard serving.

Main API areas include:

```text
/leads
/leads/{id}
/leads/export
/leads/ingest
/leads/dedupe-candidates
/leads/extract-source
/dashboard
```

---

# 🔄 End-to-End System Workflow

```text
                    ┌──────────────────────┐
                    │    Raw CSV Export    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Data Normalizer    │
                    │    import_seed.py    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   SQLite Database    │
                    │      leads.db        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
    ┌──────────────────────┐          ┌──────────────────────┐
    │   API & Dashboard    │          │   Deduplication      │
    │                      │          │                      │
    │ • Search / Filter    │          │ • Inverted Blocking  │
    │ • Update Lead        │          │ • Candidate Scoring  │
    │ • CSV Export         │          │ • Duplicate Ranking  │
    │ • Form Ingestion     │          │                      │
    └──────────┬───────────┘          └──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Source Extraction   │
    │        AI / NLP      │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ OpenRouter LLaMA 3.3 │
    │        70B           │
    └──────────┬───────────┘
               │
            fallback
               ▼
    ┌──────────────────────┐
    │   Local Regex Rules  │
    └──────────────────────┘
```

---

## 🔁 Step-by-Step Workflow

### 1. Initialization & Data Ingestion

The seed dataset contains **2,049 CRM records**.

The ingestion process:

1. Reads `data/leads_seed.csv`.
2. Normalizes names, statuses, dates, and phone numbers.
3. Extracts marketing source information from sales notes.
4. Stores the normalized records in SQLite.
5. Processes records in batches of 500.

### 2. Lead Exploration & Management

Users can manage leads through either the REST API or the web dashboard.

Supported operations include:

* Browse leads through `GET /leads`.
* Search by name, email, or company using `q`.
* Filter leads using multiple attributes.
* Update records through `PATCH /leads/{id}`.
* Automatically re-run source extraction when notes are modified.
* Export the currently filtered dataset through `GET /leads/export`.

### 3. Web Form Ingestion

The endpoint:

```text
POST /leads/ingest
```

accepts incoming website form submissions.

The workflow:

1. Validate the incoming payload.
2. Check for an existing lead using normalized email or phone number.
3. Update the existing lead when a match is found.
4. Create a new lead when no match exists.
5. Run source extraction for newly created or updated records.

### 4. Scalable Two-Stage Deduplication

The deduplication system consists of two stages.

#### Stage 1 — Blocking

Instead of comparing every record with every other record, the system creates candidate groups using:

* Normalized phone digits.
* Email domain.
* Email initial/handle.
* Cleaned company name.

This significantly reduces the number of candidate comparisons.

#### Stage 2 — Scoring

Candidate pairs are evaluated using weighted multi-attribute similarity.

The system considers:

* Name similarity.
* Email similarity.
* Phone equality.
* Company similarity.
* Company suffix normalization.

Each candidate receives:

* A confidence score.
* A match level:

  * `HIGH`
  * `MEDIUM`
  * `LOW`
* A human-readable explanation.

The current implementation processes approximately **2,000 records in under 0.5 seconds**.

### 5. AI Source Extraction

The system converts unstructured sales notes into structured marketing attribution.

Example input:

```text
Met him at the SFF booth, scanned our QR code.
```

The extraction pipeline returns:

```json
{
  "channel": "Event",
  "detail": "Singapore FinTech Festival — Booth QR Code"
}
```

The primary extraction engine uses **LLaMA 3.3 70B through OpenRouter**, with a local regex-based fallback for offline operation.

---

# ⚡ Quick Start

## 1. Prerequisites

Make sure the following are installed:

* Python 3.10+
* pip

## 2. Installation

Clone the repository and install the dependencies:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd lead_management_system

pip install -r requirements.txt
```

## 3. Environment Configuration

Create a `.env` file based on `.env.example`:

```env
DATABASE_PATH=leads.db

OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

LLM_PROVIDER=openrouter
```

> **Security:** Never commit a real API key to GitHub. Store secrets in `.env` or your deployment platform's secret manager.

Make sure `.env` is included in `.gitignore`:

```gitignore
.env
*.db
__pycache__/
.pytest_cache/
```

## 4. Seed the Database

Load and normalize the 2,049 seed records:

```bash
python3 scripts/import_seed.py
```

## 5. Run the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --port 8000
```

The application will be available at:

| Service           | URL                         |
| ----------------- | --------------------------- |
| **Web Dashboard** | http://127.0.0.1:8000/      |
| **Swagger UI**    | http://127.0.0.1:8000/docs  |
| **ReDoc**         | http://127.0.0.1:8000/redoc |

---

# 🧪 Automated Testing

Run the complete test suite:

```bash
PYTHONPATH=. pytest tests -v
```

The current test suite contains **17 test cases** covering core functionality and edge cases.

### `tests/test_leads_api.py`

Tests:

* CRUD operations.
* Multi-parameter filtering.
* Free-text search.
* Dynamic CSV export.
* Webhook form ingestion.
* Idempotent ingestion behavior.

### `tests/test_dedupe.py`

Tests:

* Candidate-pair scoring.
* Typo handling.
* Company suffix normalization.
* False-positive prevention.
* Duplicate detection logic.

### `tests/test_source_extract.py`

Tests source extraction across:

* Event Booths.
* Referrals.
* Organic Search.
* LinkedIn InMail.
* Cold Outbound.

Expected result:

```text
17/17 tests passed
```

---

# 💡 Engineering Highlights & Design Decisions

### 1. Messy Data Normalization

Built an automated data-cleaning pipeline to process **2,049 rows of raw CRM data**.

The pipeline handles:

* Missing or inconsistent names.
* Split first/last names versus full names.
* Phone number normalization.
* Seven canonical CRM statuses.
* Multiple date formats.

### 2. Scalable Two-Stage AI Deduplication

Designed an efficient deduplication system using **Inverted Index Blocking** instead of brute-force pairwise comparison.

This reduces the candidate-search complexity from approximately **O(N²)** to **O(N)** for the blocking stage and allows around **2,000 records to be scanned in under 0.5 seconds** in the current implementation.

### 3. AI-Based Source Extraction

Developed a hybrid NLP pipeline that extracts structured marketing channels and source details from unstructured sales notes.

The system uses:

* **LLaMA 3.3 70B via OpenRouter** as the primary extraction engine.
* **Local regex-based rules** as a fallback.

This design provides both AI flexibility and deterministic offline behavior.

### 4. Production-Ready REST API & Dynamic Export

Implemented a REST API supporting:

* `GET`
* `PATCH`
* `POST /leads/ingest`
* Dynamic CSV export

The API also provides automatically generated **OpenAPI/Swagger documentation**, making the service easier to test and integrate with external systems.

---

# 🔮 Future Roadmap

## 1. Semantic Vector Search for Deduplication

Introduce local vector embeddings such as:

```text
sentence-transformers/all-MiniLM-L6-v2
```

combined with a vector database such as **ChromaDB or Qdrant**.

Potential improvements include semantic matching for:

* Non-standard job titles.
* Corporate name variations.
* Similar but differently written contact information.

## 2. Interactive 3-Way Merge Tool

Build a merge interface that allows sales representatives to review duplicate records and choose which field values should be retained.

```text
Duplicate Candidate
        │
        ├── Lead A
        ├── Lead B
        └── Lead C
             │
             ▼
      Field-Level Review
             │
             ▼
        Merged Record
```

## 3. Asynchronous Background Processing

Move resource-intensive operations such as:

* Bulk CSV ingestion.
* Large-scale deduplication.
* AI source extraction.

into background workers using technologies such as:

* Celery + Redis
* ARQ + Redis

## 4. Audit Trail & Activity Log

Add field-level history tracking to record:

* Who changed a lead.
* Which fields changed.
* Previous values.
* New values.
* Timestamp of each change.

This would provide better traceability and historical provenance for CRM operations.

---

# 📌 Summary

This project demonstrates a complete AI-assisted CRM workflow combining:

* **Data normalization**
* **Scalable deduplication**
* **LLM-based information extraction**
* **REST API development**
* **Database management**
* **Automated testing**
* **Dynamic CSV export**
* **Lightweight web dashboard**

The architecture is intentionally modular, allowing individual components such as the database, LLM provider, deduplication engine, or frontend to be replaced or extended without redesigning the entire application.
