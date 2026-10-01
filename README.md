# Requirement Conflict & Overlap Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Deployment](https://img.shields.io/badge/AWS-EC2%20Ready-FF9900.svg)](DEPLOYMENT_EC2.md)

An enterprise-grade, AI-powered system engineered to audit Software Requirements Specifications (**SRS**), Business Requirements Documents (**BRD**), Functional Requirements Documents (**FRD**), and Product Requirement Documents (**PRD**).

The application extracts structured requirement clauses, maps semantic relationships, and identifies **direct logical contradictions, partial constraint mismatches, duplicates, ambiguities, and semantic overlaps** with complete document traceability.

---

## Key Differentiator: Semantic Understanding vs. Similarity

Traditional tools rely on keyword searches or naive cosine similarity, erroneously flagging similar requirements as conflicts. **ReqConflict AI** employs a two-tier semantic and formal logic pipeline:

> **Rule 17 Compliance:** The system does **not** report every semantically similar requirement as a conflict.
> - *Complementary Example:* "Users can update their email address" vs. "Users can change their profile information" are recognized as **Semantic Overlap / Consistent**, *not* a contradiction.
> - *Contradiction Example:* "Users must be logged out after 15 minutes of inactivity" vs. "Users must remain logged in for at least 30 minutes without activity" is correctly flagged as a **Critical Direct Contradiction** with differing numerical thresholds highlighted.

---

## Core Capabilities & Features

### 1. Document Ingestion & Parsing
- Supports **PDF**, Word Document (**DOCX**), and Plain Text (**TXT**).
- Automatic detection of sections, chapters, paragraphs, and manuscript page numbers.
- File validation, size limits (up to 25 MB), and secure user isolation.

### 2. Structured Requirement Extraction
- Atomic clause parsing with stable reference code generation (`SRS-001`, `BRD-014`).
- Classification into functional domains: *Authentication & Security*, *Authorization & Access*, *Business & Transaction*, *Performance & Scalability*, etc.
- Priority derivation (*Must Have / High*, *Should Have / Medium*, *Could Have / Low*).

### 3. Deep Semantic Analysis Engine
- **Direct Contradictions (Critical/High):** Incompatible authorization flows (e.g. self-service email reset vs. mandatory administrator verification), numerical timing mismatches (15 min vs 30 min session timeouts, 14 days vs 30 days refund windows), and opposing logical directives (permissive vs. prohibitive).
- **Partial Conflicts (Medium):** Conflicting workflow boundaries (e.g. event-based cancellation upon shipment vs. fixed 2-hour elapsed cancellation windows).
- **Semantic Overlaps (Low):** Functionally identical operations described with distinct terminology (e.g. "cancel an order before shipment" vs. "orders may be cancelled until dispatch").
- **Duplicates (Low):** Redundant specification of the same security control across multiple documents (e.g. mandatory 2FA for administrators).
- **Ambiguity Detection (Medium):** Flags subjective, non-verifiable terms (e.g. *"quickly"*, *"high traffic"*, *"user-friendly"*) and provides quantifiable SLA suggestions.

### 4. Side-by-Side Requirement Comparison & Traceability
- Side-by-side inspection view:
  - **Left Card:** Requirement ID, source document, section, page, original text quote.
  - **Right Card:** Requirement ID, source document, section, page, original text quote.
  - **Conflict Analysis Breakdown:** Concise explanation, exact conflicting elements, and suggested neutral clarification.
- Full traceability: Click any reference tag (`SRS-004`) to jump directly to that requirement in the registry.

### 5. Enterprise Dashboard & Visualizations
- Real-time telemetry cards (Documents, Requirements, Detected Findings, Critical Contradictions, Semantic Overlaps).
- Interactive **Chart.js** visualizations:
  - Severity Breakdown (Donut)
  - Findings by Relationship Type (Horizontal Bar)
  - Conflicts by Source Document (Stacked Bar)
- Priority Conflicts action table with one-click side-by-side modal launcher.

### 6. Authentication & User Isolation
- Integrated **Firebase Authentication**:
  - Google Sign-In
  - Apple Sign-In
  - Interactive Demo Workspace Mode (one-click guest evaluation)
  - Protected routes and token verification.

### 7. Audit Reports & Deliverables
- Executive audit report view.
- One-click exports in **CSV**, **JSON**, and **Markdown**.
- Print-ready and Save to PDF styling.

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │   Enterprise Single Page UI (SPA)    │
                      │   Vanilla CSS, JS, Chart.js, Lucide  │
                      └──────────────────┬───────────────────┘
                                         │ REST API / Bearer Token
                                         ▼
                      ┌──────────────────────────────────────┐
                      │       FastAPI Backend Application    │
                      └───────┬──────────────────────┬───────┘
                              │                      │
             ┌────────────────▼─────────┐  ┌─────────▼──────────────┐
             │ Multi-Format Parsers     │  │ Modular AI Engine      │
             │ - pypdf (PDF)            │  │ - Smart Local NLP      │
             │ - python-docx (DOCX)     │  │ - OpenAI (GPT-4o-mini) │
             │ - Text/Structure Parser  │  │ - Google Gemini Flash  │
             └────────────────┬─────────┘  └─────────┬──────────────┘
                              │                      │
                              ▼                      ▼
                      ┌──────────────────────────────────────┐
                      │ SQLite / WAL DB + User Data Storage  │
                      │ Documents, Reqs, Traceable Conflicts │
                      └──────────────────────────────────────┘
```

---

## Project Structure

```
requirement_contradiction_dector/
├── backend/
│   ├── app/
│   │   ├── api/                     # REST API Routers
│   │   │   ├── auth.py              # Firebase Auth & verification
│   │   │   ├── documents.py         # Document upload, parse, list, delete
│   │   │   ├── requirements.py      # Requirements registry & search
│   │   │   ├── conflicts.py         # Conflict detection & export
│   │   │   ├── settings.py          # AI Provider configuration
│   │   │   └── demo.py              # Instant sample data loader
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic data schemas
│   │   ├── services/
│   │   │   ├── auth_service.py      # Token validation & session
│   │   │   ├── document_parser.py   # PDF, DOCX, TXT structure parser
│   │   │   ├── requirement_extractor.py # Regex + semantic clause chunking
│   │   │   ├── conflict_analyzer.py # Pairwise analysis orchestration
│   │   │   ├── report_service.py    # CSV, JSON, Markdown generator
│   │   │   └── ai_providers/
│   │   │       ├── base.py          # Abstract Provider interface
│   │   │       ├── smart_local.py   # Offline smart semantic NLP engine
│   │   │       ├── openai_provider.py # OpenAI GPT integration
│   │   │       ├── gemini_provider.py # Gemini Flash integration
│   │   │       └── provider_factory.py# Provider selector factory
│   │   ├── config.py                # Environment & paths config
│   │   ├── database.py              # SQLite schema & thread-safe DB
│   │   └── main.py                  # FastAPI app entry point & SPA mount
├── frontend/
│   ├── index.html                   # Enterprise Single Page Application
│   ├── css/
│   │   ├── main.css                 # Dark mode design system & tokens
│   │   └── components.css           # Side-by-side modal, tables, dropzone
│   └── js/
│       ├── api.js                   # Authenticated REST client
│       ├── auth.js                  # Firebase Google/Apple & Demo login
│       ├── dashboard.js             # Metrics & Chart.js graphs
│       ├── documents.js             # Upload dropzone & document list
│       ├── requirements.js          # Registry browser & search
│       ├── conflicts.js             # Findings table & filters
│       ├── comparison.js            # Side-by-side modal controller
│       ├── reports.js               # Report view & export triggers
│       ├── settings.js              # AI provider switcher
│       └── app.js                   # Application coordinator & routing
├── sample_data/
│   ├── E-Commerce_Platform_SRS.txt  # Sample SRS text
│   ├── E-Commerce_Platform_SRS.pdf  # Sample SRS PDF
│   ├── E-Commerce_Platform_SRS.docx # Sample SRS DOCX
│   ├── E-Commerce_Business_Requirements_BRD.txt
│   ├── E-Commerce_Business_Requirements_BRD.pdf
│   ├── E-Commerce_Business_Requirements_BRD.docx
│   └── generate_sample_docs.py      # Sample files generator script
├── deployment/
│   ├── Dockerfile                   # Production container build
│   ├── docker-compose.yml           # Multi-container service
│   ├── nginx.conf                   # Reverse proxy configuration
│   ├── requirement-analyzer.service # Systemd service unit
│   └── deploy_ec2.sh                # Automated AWS EC2 setup script
├── run_server.py                    # Server startup script
├── test_analyzer.py                 # Automated verification test script
├── DEPLOYMENT_EC2.md                # AWS EC2 production deployment guide
├── requirements.txt                 # Backend Python dependencies
└── .env.example                     # Environment template
```

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+ installed
- pip

### 2. Installation
```bash
# Clone the repository
cd requirement_contradiction_dector

# Install dependencies
pip install -r requirements.txt

# Start the application server
python run_server.py
```

### 3. Open in Browser
Open [http://localhost:8000](http://localhost:8000) in your web browser:
1. Click **"Try Interactive Demo Workspace"** (or sign in via Google / Apple).
2. The Dashboard will immediately load with sample SRS and BRD telemetry.
3. Test uploading your own requirement documents in the **Documents** tab!

### 4. Running Verification Tests
To run the automated analysis test suite:
```bash
python test_analyzer.py
```

---

## AWS EC2 Production Deployment

The project is production-ready for deployment on an **AWS EC2 Linux instance** (Ubuntu 22.04/24.04 LTS or Amazon Linux 2023).

For complete step-by-step instructions, see [DEPLOYMENT_EC2.md](DEPLOYMENT_EC2.md).

Quick setup on your EC2 instance:
```bash
git clone <YOUR_REPO_URL> requirement-analyzer
cd requirement-analyzer
chmod +x deployment/deploy_ec2.sh
bash deployment/deploy_ec2.sh
```

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
