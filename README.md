# ThreadTrace

An AI memory assistant for education-support NGOs and mentors. Remembers
student case history, missing documents, deadlines, and follow-up actions
across multiple volunteers and sessions.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env: add your Cognee Cloud COGNEE_SERVICE_URL and COGNEE_API_KEY
# (sign up at Cognee Cloud, claim the dev credit with code COGNEE-35,
# generate an API key from the API Keys page in the console)
```

## Run

```bash
streamlit run app.py
```

## Load demo data (do this before your first real test/demo)

```bash
python seed/demo_seed.py
```

## Project structure

```
ThreadTrace/
├── app.py                      # Landing page + summary metrics
├── pages/
│   ├── 1_Add_Case.py           # Create a new student case
│   ├── 2_Add_Followup.py       # Log a call/visit -> calls cognee remember()
│   ├── 3_Ask_ThreadTrace.py     # Query memory -> calls cognee recall()
│   ├── 4_Dashboard.py          # Urgent / overdue / deadline views
│   └── 5_Close_Purge_Case.py   # Close (soft) or Purge (hard delete, forget())
├── services/
│   ├── cognee_service.py       # All Cognee remember/recall/forget calls
│   ├── storage_service.py      # Local JSON storage for structured data
│   └── query_service.py        # Derived logic: urgency, overdue calculations
├── seed/
│   └── demo_seed.py            # Generates 5 demo cases + follow-ups
└── data/                       # cases.json, documents.json, followups.json
```

## Key design decisions

- **Only follow-up notes go into Cognee.** StudentCase and Document fields
  are structured data with no unstructured text worth a knowledge graph —
  they live in local JSON only. This keeps the Cognee usage honest: recall()
  answers from real ingested text, not re-served structured fields.
- **One Cognee dataset per case** (`case_<id>`). This is what makes
  `forget_case()` a clean, scoped purge instead of an all-or-nothing wipe.
- **Urgency is computed, not stored.** A case is urgent if its deadline is
  within 5 days OR it hasn't had a follow-up in 10+ days. See
  `query_service.py` to change these thresholds.
- **Close vs Purge are two different actions.** Close = soft status change,
  data stays. Purge = hard delete from local storage AND Cognee memory —
  this is the actual `forget()` demo moment.

## Demo script :)

1. Show the dashboard with seeded cases — urgent ones flagged.
2. Add a follow-up note live for one case.
3. Ask: *"Summarize [student]'s case and what's still pending."*
4. Ask across all cases: *"Who hasn't been followed up in 10 days?"*
5. Purge a closed case — show it's actually gone from memory.
