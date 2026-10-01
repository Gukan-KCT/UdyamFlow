# PROGRESS.md

## Current Phase: Single-Window Approval & Compliance Portal (UdyamFlow) — Complete

---

## Completed Phases (SIH 2026 Single-Window Portal)

- [x] **Phase 0 (Foundation & Hygiene):**
  - Git cleanup, `.env` protection, case-insensitive collision fix (`app.ai`).
  - Dynamic clock with `DEMO_NOW` support, multi-provider AI architecture (Ollama / OpenRouter / Rule-based Fallback).
  - Modern FastAPI lifespan context manager, dynamic CORS, standardized JSON error envelopes.
  - Comprehensive automated pytest suite (31 tests baseline) and clean Vite production build.

- [x] **Phase 1 (Data Model, Auth, Roles, RBAC, Audit):**
  - Database schema expanded with tables for `departments`, `users`, `business_profiles`, `approval_catalogue`, `applications`, `application_approvals`, `documents`, `document_versions`, `verified_data_store`, `queries`, `inspections`, `certificates`, `renewals`, `compliance_tasks`, `schemes`, `scheme_applications`, `grievances`, `audit_log`, `notifications`.
  - Cryptographic PBKDF2-HMAC-SHA256 password hashing + salt (`app/auth/security.py`).
  - HMAC-SHA256 signed bearer tokens with expiry.
  - Strict RBAC: `applicant`, `dept_officer`, `senior_officer`, `nodal_officer`, `admin`.
  - Immutable audit trail (`app/audit/audit_service.py`) logging actor, action, entity, before/after states, reason, and IP.
  - Comprehensive seed data for departments, roles, demo users (`Demo@123`), and sample profile (`app/seed/seed_data.py`).

- [x] **Phase 2 (Regulatory Knowledge Engine & Dynamic Checklist):**
  - Approval Catalogue with sector, scale, stage, and location-type rules.
  - Explicit `"SAMPLE / ILLUSTRATIVE - VERIFY AGAINST OFFICIAL SOURCES"` disclaimers.
  - Dynamic checklist generator calculating critical-path composite SLA (parallel processing) and unified fee.

- [x] **Phase 3 (Single Window Application & Parallel Workflow Orchestrator):**
  - Composite multi-department application submission (`/api/applications`).
  - Parallel sub-approvals for departments running concurrently.
  - Department officer review, clarification query loop management, approval sign-off, and digital certificate generation.

- [x] **Phase 4 (Document Vault, Pre-Validation & Smart Form Autofill):**
  - Applicant document vault with format/size verification (max 15MB) and SHA256 integrity hashes.
  - Pre-validation engine with 0-100% readiness score, detecting missing and expired documents.
  - Smart autofill suggestions from verified data store (PAN, GSTIN, Udyam registration).

- [x] **Phase 5 (Common Inspection Scheduling & Joint Reporting):**
  - Multi-department joint site visit coordination replacing disjointed visits.
  - Inspection slot scheduling and joint report submission with observations and pass/conditional/fail verdict.

- [x] **Phase 6 (Grievance Redressal, SLA Escalation & Delay Analytics Wiring):**
  - Multi-tier grievance redressal with automated statutory SLA tracking: Level 1 (Dept Nodal) → Level 2 (District Collector) → Level 3 (State Appellate).
  - Delay Analytics module re-wired directly to application approvals to detect stuck files (>7 days), query loops, and imminent SLA breaches with AI/rule unblockers.
  - Departmental bottleneck benchmarking (workload, query rate %, approval rate %, SLA adherence).

- [x] **Phase 7 (Compliance Calendar, Renewals & Incentives/Schemes):**
  - Post-establishment compliance calendar for recurring returns (Pollution, Labour, Fire safety).
  - Upcoming renewal alerts (30/60/90 days).
  - Verifiable digital certificates with public QR registry lookup.
  - Industrial Policy Incentives engine: Capital subsidy, power concessions, stamp duty exemptions claim filing.

- [x] **Phase 8 (Frontend Portal & Demo Polish):**
  - UdyamFlow single-window portal with responsive navigation and statutory emblem styling.
  - TopBar interactive persona switcher for rapid 1-click live demo across Applicant, PCB Officer, Fire Officer, Nodal Authority, and Admin.
  - Specialized portal views: Checklist Wizard, Composite Applications, Document Vault, Common Inspections, Compliance Calendar, Schemes & Incentives, Grievances, and Delay Analytics Radar.
  - Retained legacy e-Office file radar and org tree for complete backward compatibility.
  - Verified 100% test pass rate (41 tests passing) and clean frontend production build (`vite build`).

---

## Codebase State

### Backend (src/backend/)

| File | Status |
|---|---|
| config.py | Done — thresholds, REFERENCE_NOW, AI_PROVIDER (ollama/openrouter/none) |
| main.py | Done — CORS, non-blocking on-demand startup pipeline |
| app/models.py | Done — Employee, FileRecord, Event, Alert, AiInsight, ConsolidatedAlert |
| app/db.py | Done — SQLite operations |
| app/ai/assistant.py | Done — Smart Query Router, Intent classification, Name resolution |
| app/ai/assistant_prompts.py | Done — Intent-specific dynamic prompts |
| app/ai/ollama_service.py | Done — Ollama client and multi-provider dispatcher with fallback |
| app/ai/openrouter_service.py | Done — async httpx OpenRouter integration with fallback |
| app/core/orchestrator.py | Done — on-demand insight generation with caching |
| app/api/routes.py | Done — integrated assistant chat and all core endpoints |
| tests/ | In Progress / Passing |

### Data (src/backend/data/)

| File | Status |
|---|---|
| employee.csv | Present — 10 employees |
| files.csv | Present — 35 files (31 Active, 4 Closed) |
| events.csv | Present — 250 events |
| filepulse.sqlite3 | Live — populated by startup pipeline |

### Frontend (src/frontend/src/)

| File | Status |
|---|---|
| components/AssistantPanel.jsx | Done — UI Drawer with URL-aware context payload |
| api/client.js | Done — fetch commands wired to Railway prod |
| vercel.json | Done — Proxy rewrites for `/api` |

---

## Decisions Log

| Time | Decision | Reason |
|---|---|---|
| 2026-08-08 | REFERENCE_NOW = 2025-03-18T09:00:00 | Frozen clock for reproducible demo |
| 2026-08-08 | Calendar-day math (.date() subtraction) | Feb 1 → Mar 18 = 45 days exact |
| 2026-08-09 | Migrate to OpenRouter API | Cloud deployment (Railway) required an accessible LLM endpoint since local Ollama doesn't scale to PaaS directly. |
| 2026-08-09 | On-Demand AI Generation | Pre-generating insights on boot caused Railway to timeout (502). Async on-demand solves this. |
| 2026-08-09 | Context-Aware AI Routing | Enhance UX so the LLM intuitively knows which file the user is viewing when the drawer opens. |

---

## Next Up

1. **Monitor Deployments** — Verify long-term stability of the Railway & Vercel deployment.
2. **Review Feedback** — Check if Mr. Iyer requires any UX/UI polishing on the dashboard components.
