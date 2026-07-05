# 🌉 ThreadTrace

**AI-powered case memory for NGO education support workers**

ThreadTrace helps volunteers manage student scholarship and admission cases without losing context. Every follow-up note, document update, and case event is stored locally and committed to **Cognee Cloud** as AI memory — so any volunteer can instantly recall the full history of any case, get suggested next actions, and surface risks across the entire caseload.

---

## What's Inside

```
threadtrace/
├── app.py                      # Home — metrics, activity feed, AI daily briefing
├── pages/
│   ├── 1_Add_Case.py           # Register a new student case
│   ├── 2_Add_Followup.py       # Log a call, visit, or message
│   ├── 3_Case_Detail.py        # Full case view + AI memory panel
│   ├── 4_Ask_ThreadTrace.py    # Natural language queries over all cases
│   ├── 5_Search.py             # Keyword + AI semantic search
│   ├── 6_Dashboard.py          # Urgent cases, volunteers, activity feed
│   ├── 7_Reports.py            # Stats, AI insights, CSV export
│   └── 8_Close_Purge.py        # Close or permanently purge a case
├── services/
│   ├── cognee_service.py       # All Cognee Cloud integration (AI memory)
│   ├── storage_service.py      # Local JSON storage for cases, docs, follow-ups
│   └── query_service.py        # Urgency logic, reports, CSV export
├── utils/
│   ├── helpers.py              # Shared UI components
│   └── styles.py               # Global CSS
├── seed/
│   └── demo_seed.py            # Loads 5 demo cases with follow-ups into the app
├── data/                       # Auto-created — cases.json, documents.json, followups.json
├── .env.example                # Credential template
└── requirements.txt
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add your credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your Cognee Cloud details:

```env
COGNEE_BASE_URL=https://your-tenant.aws.cognee.ai
COGNEE_API_KEY=ck_your_key_here
```

> Sign up at [cognee.ai](https://cognee.ai)

### 3. Load demo data

Run this once before your first use or demo. It creates 5 realistic student cases with documents and follow-ups, and seeds everything into Cognee memory so AI features work immediately.

```bash
python seed/demo_seed.py
```

### 4. Run the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Key Features

- **Case management** — create and track student cases with documents, deadlines, and assigned volunteers
- **Follow-up logging** — log every call, visit, or message; each one is committed to Cognee AI memory
- **AI case intelligence** — per-case summary, next action suggestion, blocker extraction, timeline reconstruction, and risk assessment powered by Cognee recall
- **Natural language querying** — ask questions across one case or your entire caseload
- **Semantic search** — search inside follow-up notes and context, not just structured fields
- **Dashboard** — live urgency tracking, overdue follow-ups, volunteer workload, AI briefing
- **Reports & export** — charts, AI caseload insights, and CSV export for cases and follow-ups
- **Safe deletion** — close cases softly or purge them permanently from both storage and Cognee memory

---

## 📖 Documentation

For the complete architecture, Cognee integration, setup guide, and technical details, see [DOCUMENTATION.md](DOCUMENTATION.md).