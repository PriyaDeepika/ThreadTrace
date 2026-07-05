# 🌉 ThreadTrace

> **AI-powered case memory for NGO education support workers**

ThreadTrace helps NGO volunteers manage student scholarship and admission cases over time. It uses **Cognee Cloud** as its AI memory backbone — so every follow-up note, document update, and case event is remembered, recalled, and reasoned over by AI. No student falls through the cracks because of lost context.

---

## Table of Contents

- [The Problem It Solves](#the-problem-it-solves)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Pages & Features](#pages--features)
- [Cognee AI Integration](#cognee-ai-integration)
- [Data Model](#data-model)
- [Setup & Installation](#setup--installation)
- [Running the App](#running-the-app)
- [Loading Demo Data](#loading-demo-data)
- [Environment Variables](#environment-variables)
- [Architecture Decisions](#architecture-decisions)
- [Demo Script](#demo-script-90-seconds)

---

## The Problem It Solves

NGO volunteers managing student cases face a recurring problem: **context loss**. When a volunteer returns to a case after a week, or when a different volunteer takes over, critical information is gone — what was promised in the last call, which documents are still missing, what the blocker was, what the student's situation is.

This plays out every day:
- Volunteers asking students to repeat their story on every contact
- Deadlines missed because no one remembered the follow-up
- Documents submitted twice, or not at all, because status was unclear
- No institutional memory when a volunteer leaves

ThreadTrace solves this by giving every volunteer **instant AI-generated context** on any case, at any time — powered by a knowledge graph built from every interaction logged in the system.

---

## How It Works

```
Volunteer logs a follow-up note
          ↓
ThreadTrace saves it locally (JSON) + sends it to Cognee Cloud
          ↓
Cognee builds/updates a knowledge graph for that case
          ↓
Next time any volunteer opens the case:
  → AI generates a case summary
  → AI suggests the next action
  → AI surfaces pending blockers
  → AI reconstructs the timeline
  → AI assesses risk level
```

Every piece of text that enters the system — case creation notes, follow-up logs, document status changes, closing notes — is ingested into Cognee's memory. From that point on, any volunteer can ask natural language questions and get answers grounded in the full case history.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| AI Memory | Cognee Cloud (knowledge graph + vector store) |
| Local Storage | JSON files (cases, documents, follow-ups) |
| Language | Python 3.12 |
| Async runtime | asyncio + persistent background event loop |
| Styling | Custom CSS via `st.markdown` + `utils/styles.py` |

---

## Project Structure

```
threadtrace/
│
├── app.py                        # Home page — metrics, activity feed, AI briefing
├── main.py                       # Entry point alias
│
├── pages/
│   ├── 1_Add_Case.py             # Register a new student case
│   ├── 2_Add_Followup.py         # Log a call/visit/message
│   ├── 3_Case_Detail.py          # Full case view + AI memory panel
│   ├── 4_Ask_ThreadTrace.py      # Natural language querying over all cases
│   ├── 5_Search.py               # Keyword + AI semantic search
│   ├── 6_Dashboard.py            # Live dashboard — urgent, overdue, volunteers
│   ├── 7_Reports.py              # Statistics, AI insights, CSV export
│   └── 8_Close_Purge.py          # Close (soft) or purge (hard delete + forget)
│
├── services/
│   ├── cognee_service.py         # ALL Cognee Cloud integration (memory layer)
│   ├── storage_service.py        # Local JSON CRUD — cases, documents, follow-ups
│   └── query_service.py          # Computed logic — urgency, workload, reports, CSV
│
├── utils/
│   ├── helpers.py                # Shared UI components and formatting functions
│   └── styles.py                 # Global CSS design system
│
├── seed/
│   └── demo_seed.py              # Loads 5 realistic demo cases + follow-ups
│
├── data/
│   ├── cases.json                # All student case records
│   ├── documents.json            # Document records per case
│   └── followups.json            # Follow-up logs per case
│
├── .env                          # Your credentials (never commit this)
├── .env.example                  # Template showing required variables
└── requirements.txt              # Python dependencies
```

---

## Pages & Features

### 🏠 Home (`app.py`)
The command centre. Shows at a glance:
- **5 live metrics** — active cases, urgent, overdue follow-ups, missing documents, closed
- **Recent activity feed** — last 10 follow-ups across all cases with blocker highlights
- **AI Daily Briefing** — one click generates a Cognee-powered briefing of today's priorities
- **Needs Attention** — urgent cases listed with deadline and volunteer
- **Quick action links** — shortcuts to every page

---

### ➕ Add Case (`1_Add_Case.py`)
Registers a new student case with:
- Student details (name, age, location, contact, education level)
- Case details (goal, target program/scholarship, deadline, assigned volunteer)
- Initial notes
- Document checklist with initial status

**On submission:** creates the local record AND immediately seeds Cognee memory with the case context — so AI features work from the very first interaction, before any follow-up is logged.

Also has an **All Cases tab** with status/volunteer/goal filters and sortable table view.

---

### 📝 Add Follow-Up (`2_Add_Followup.py`)
The most-used page. Logs every volunteer-student interaction:
- Case selector (active cases only)
- Interaction type — call, visit, WhatsApp/SMS, email
- Free-text note (what happened, what was discussed)
- Blocker field (what's preventing progress)
- Next action field (what was promised)
- Next follow-up date scheduler

**AI Pre-Briefing:** before filling the form, volunteers can click "What should I cover?" — Cognee reads the case memory and suggests the most important thing to address in this contact.

**On submission:** saves locally AND commits to Cognee memory in one action.

Right panel shows a case snapshot (location, goal, deadline, documents) and the last 3 follow-ups for quick reference.

---

### 🗂️ Case Detail (`3_Case_Detail.py`)
Full view of a single case. Two-column layout:

**Left column:**
- Status bar (urgency badge, deadline, volunteer, missing doc count)
- Editable case fields (all fields can be updated in-place)
- Document management — add, update status, delete documents. Every status change is sent to Cognee memory.
- Follow-up history with delete — plus a Quick Follow-Up form to log without leaving the page

**Right column — AI Memory Panel (6 buttons):**

| Button | What Cognee does |
|---|---|
| Generate Case Summary | Summarises everything known about this case in bullet form |
| Suggest Next Action | Recommends the single most important next step |
| Extract Pending Blockers | Lists all unresolved obstacles mentioned across all follow-ups |
| Summarise Timeline | Reconstructs the case chronologically from memory |
| Assess Risk Level | Rates Low/Medium/High risk of the student not meeting their goal |
| Ask (free-form) | Any question about this specific case |

All AI results are cached in `st.session_state` — clicking a button once keeps the result visible without re-querying Cognee on every page interaction.

---

### 💬 Ask ThreadTrace (`4_Ask_ThreadTrace.py`)
Natural language querying in three modes:

**Single Case tab** — ask anything about one specific case:
- Quick-select example questions (pre-filled into the input)
- Free-form text input
- Results cached in session query history

**Across All Cases tab** — cross-case reasoning:
- Choose scope (active only, or all cases)
- 7 quick-query buttons for common questions
- Free-form input for anything else

**Preset Queries tab** — six analytical queries that surface patterns impossible to find manually:
- Extract All Active Blockers
- Identify At-Risk Cases
- Missing Document Analysis
- Volunteer Workload Intelligence
- Recurring Patterns
- Success Signals

Query history is shown at the bottom of the page for the current session.

---

### 🔎 Search (`5_Search.py`)
Two-layer search:

**Keyword search** — instant, local, searches across: student name, location, volunteer, program, case ID, summary. Results show as case cards with urgency badge.

**AI Semantic Search** — powered by Cognee. Searches inside the actual content of follow-up notes, blockers, and promises — not just structured fields. Example: searching *"cases where family hasn't visited the village office"* will find cases where that specific situation was mentioned in a note, even if the word "village office" doesn't appear in any structured field.

**Find Similar Cases** — select a reference case, Cognee searches for other cases with similar blockers, goals, or situations.

---

### 📊 Dashboard (`6_Dashboard.py`)
Four tabs:

**Overview** — urgent cases with urgency badges, deadline tracker (overdue + this week), overdue follow-up table with days-since count.

**Volunteers** — workload table (cases, urgent count, overdue count per volunteer), expandable per-volunteer case breakdown, AI volunteer intelligence button.

**Activity Feed** — all follow-ups across all cases, filterable by worker, with type colour-coding (call/visit/message/email).

**AI Briefing** — four on-demand Cognee analyses:
- Today's Priority Cases
- Common Blockers Across Cases
- At-Risk Case Identification
- Full Caseload Summary

All results are cached per session.

---

### 📋 Reports (`7_Reports.py`)
Three tabs:

**Statistics** — bar charts for cases by goal, cases by location (top 10), deadline status breakdown, follow-up activity over the last 14 days, volunteer workload table, missing documents breakdown with per-student table.

**AI Insights** — five preset Cognee analyses over the entire caseload:
- Full Caseload Summary
- Systemic Blockers
- Risk Analysis
- What's Working
- Process Recommendations

Plus a custom query box for ad-hoc analysis.

**Export** — one-click CSV download for all cases and all follow-ups. Preview table shows all cases with follow-up counts and missing doc counts.

---

### 🗑️ Close / Purge (`8_Close_Purge.py`)
Two distinct actions, clearly separated:

**Close (soft)** — marks a case as resolved. All data and Cognee memory are retained. Can be re-opened. Optionally records a closing note which is also committed to Cognee memory.

**Purge (hard delete)** — requires typing the student's name to confirm. Permanently deletes:
- The case record from local JSON
- All documents and follow-ups from local JSON
- The entire case dataset from Cognee Cloud (`forget()` API call)

This is the real `forget()` demo — verifiable deletion from both storage systems.

Also shows a full case history expander before acting, and an AI pre-closure summary so no context is lost before deletion.

---

## Cognee AI Integration

Cognee is the core AI layer. It's not a chatbot wrapper — it's a knowledge graph that remembers the full context of every case and reasons across it.

### Where Cognee is called

| Action | Cognee function | What it does |
|---|---|---|
| Case created | `remember_case_context()` | Seeds initial case context into memory |
| Follow-up logged | `remember_followup()` | Ingests full interaction — note, blocker, next step, worker, type |
| Document status changed | `remember_document_update()` | Keeps memory current with document progress |
| Case Detail → Summary | `summarize_case()` | Bullet summary of the full case |
| Case Detail → Next Action | `suggest_next_action()` | Single most important action to take |
| Case Detail → Blockers | `recall_case()` | Extracts all unresolved blockers |
| Case Detail → Timeline | `recall_case()` | Chronological reconstruction |
| Case Detail → Risk | `recall_case()` | Risk rating with explanation |
| Case Detail → Ask | `recall_case()` | Free-form question about this case |
| Dashboard → AI Briefing | `recall_urgent_context()` | Cross-case urgency summary |
| Ask → single case | `recall_case()` | Question scoped to one case |
| Ask → all cases | `recall_across_cases()` | Cross-dataset graph reasoning |
| Search → semantic | `semantic_search()` | Searches inside note content |
| Reports → insights | `generate_insights()` | Caseload-wide pattern analysis |
| Close/Purge → purge | `forget_case()` | Hard delete from Cognee memory |

### Dataset scoping

Each case gets its own Cognee dataset named `case_<case_id>`. This means:
- Recall queries can be scoped to a single case (fast, precise)
- Or fanned out across multiple datasets for cross-case reasoning
- `forget()` deletes exactly one case's memory without touching others

### Event loop (Windows compatibility)

Cognee uses `aiohttp` for HTTP to Cognee Cloud. On Windows with Python 3.12, `asyncio.run()` closes the event loop after each call, and `aiohttp` fails on the next call with `Event loop is closed`. ThreadTrace solves this by running a single persistent event loop in a background daemon thread and submitting all coroutines to it via `asyncio.run_coroutine_threadsafe()`.

---

## Data Model

### StudentCase
```
case_id                       string (8-char UUID prefix)
student_name                  string
location                      string
goal                          enum: Scholarship | Admission support | Fee reimbursement |
                                    Hostel support | Fee concession | Other
target_program_or_scholarship string
deadline                      ISO date string
status                        enum: active | closed
assigned_volunteer            string
summary                       string (free text notes)
contact_number                string (optional)
age                           string (optional)
education_level               string (optional)
created_at                    ISO datetime
updated_at                    ISO datetime
closed_at                     ISO datetime | null
```

### Document
```
doc_id      string
case_id     string (FK → StudentCase)
doc_name    string (e.g. Income certificate, Caste certificate, SOP)
status      enum: submitted | missing | pending_verification
notes       string (optional context)
created_at  ISO datetime
updated_at  ISO datetime
```

### FollowUp
```
followup_id        string
case_id            string (FK → StudentCase)
date               ISO datetime
worker_name        string
note_text          string (the main free-text log — this is what Cognee ingests)
blockers           string (what's preventing progress)
next_step          string (what was promised)
next_followup_date ISO date | null
followup_type      enum: call | visit | message | email
```

### Urgency Logic (computed, never stored)
A case is flagged urgent if:
- Its deadline is within **5 days**, OR
- It has had no follow-up in **10 or more days**

Urgency is always computed fresh from real dates — never a manually-set status that can go stale.

---

## Setup & Installation

### Prerequisites
- Python 3.10 or higher
- A Cognee Cloud account with an API key (sign up at [cognee.ai](https://cognee.ai), use code `COGNEE-35` for a free Developer plan)

### 1. Clone or unzip the project
```bash
cd threadtrace
```

### 2. Create a virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
```

Edit `.env` and fill in your Cognee Cloud credentials:
```env
COGNEE_BASE_URL=https://your-tenant.aws.cognee.ai
COGNEE_API_KEY=ck_your_api_key_here
```

---

## Running the App

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` by default.

---

## Loading Demo Data

Before your first use or demo, load five realistic student cases with documents and follow-ups pre-seeded into both local storage and Cognee memory:

```bash
python seed/demo_seed.py
```

This creates:
- **5 student cases** — Anjali Reddy (scholarship, urgent deadline), Ravi Kumar (fee reimbursement), Priya Shaik (nursing admission, most urgent), Naveen Babu (polytechnic scholarship), Sushmita Rao (fee concession)
- **10+ documents** across all cases with realistic statuses
- **12+ follow-up notes** across all cases with blockers and next steps
- All content ingested into Cognee memory so AI features work immediately

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `COGNEE_BASE_URL` | Yes | Your Cognee Cloud tenant URL |
| `COGNEE_API_KEY` | Yes | Your Cognee Cloud API key |

The app runs without Cognee configured — all local features (case management, documents, follow-ups, filters, CSV export) work fully. AI features show a "Cognee not configured" banner and are disabled until credentials are added.

---

## Architecture Decisions

**Why separate local storage from Cognee?**
Local JSON handles structured queries (filter by volunteer, sort by deadline, count missing docs). These are exact field lookups that don't need a knowledge graph. Cognee handles the unstructured layer — follow-up notes, blockers, promises — where graph traversal and semantic similarity add real value. Mixing them would mean using a knowledge graph for tasks it's not suited for, and would make the dashboard slow.

**Why one Cognee dataset per case?**
It enables scoped recall (fast, no cross-contamination between cases) and clean deletion via `forget()`. A single global dataset would mean purging one student's data requires deleting everything.

**Why JSON files instead of a database?**
For a hackathon/MVP context, JSON files mean zero setup, easy inspection, and trivial portability. The storage layer is fully abstracted behind `storage_service.py` — swapping to SQLite or PostgreSQL requires only changing `_load` and `_save`, with no changes to any page or service.

**Why a persistent background event loop?**
Cognee's cloud client uses `aiohttp`, which creates an event loop-bound connector. On Windows with Python 3.12, `asyncio.run()` closes the loop after each call. Running a permanent loop in a daemon thread and using `run_coroutine_threadsafe()` avoids the `Event loop is closed` crash while keeping all Streamlit page code synchronous.

**Why is urgency computed and not stored?**
A stored urgency flag goes stale the moment a follow-up is logged or a deadline passes without anyone updating the flag. Computing it fresh on every page load from real dates means the dashboard is always accurate, not reliant on volunteers remembering to update a status field.

---