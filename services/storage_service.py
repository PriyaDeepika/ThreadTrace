"""
storage_service.py — Local structured data layer for ThreadTrace.

Stores StudentCase, Document, FollowUp in flat JSON files.
This layer is separate from Cognee — it holds structured/queryable data
(exact field lookups, filtering, sorting). Cognee holds unstructured
memory (notes, context, history for AI recall).

Upgrade path: replace _load/_save with SQLite — function signatures unchanged.
"""

import json
import os
import uuid
from datetime import datetime, date
from typing import Optional

DATA_DIR       = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CASES_FILE     = os.path.join(DATA_DIR, "cases.json")
DOCUMENTS_FILE = os.path.join(DATA_DIR, "documents.json")
FOLLOWUPS_FILE = os.path.join(DATA_DIR, "followups.json")

VALID_STATUSES     = ["active", "closed"]
VALID_DOC_STATUSES = ["submitted", "missing", "pending_verification"]
GOALS              = ["Scholarship", "Admission support", "Fee reimbursement",
                      "Hostel support", "Fee concession", "Other"]
COMMON_DOCS        = ["Income certificate", "Caste certificate", "Marks memo",
                      "Aadhaar card", "Recommendation letter", "SOP",
                      "Bank passbook copy", "Counseling fee receipt",
                      "Previous fee receipt", "ID proof", "Other"]
FOLLOWUP_TYPES     = ["call", "visit", "message", "email"]


# ── file helpers ──────────────────────────────────────────────────────────────

def _ensure_file(path: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)

def _load(path: str) -> list:
    _ensure_file(path)
    with open(path) as f:
        return json.load(f)

def _save(path: str, records: list):
    _ensure_file(path)
    with open(path, "w") as f:
        json.dump(records, f, indent=2, default=str)


# ── StudentCase ───────────────────────────────────────────────────────────────

def create_case(student_name: str, location: str, goal: str,
                target_program_or_scholarship: str, deadline: str,
                assigned_volunteer: str, summary: str = "",
                contact_number: str = "", age: str = "",
                education_level: str = "") -> dict:
    cases = _load(CASES_FILE)
    case = {
        "case_id":                       str(uuid.uuid4())[:8],
        "student_name":                  student_name.strip(),
        "location":                      location.strip(),
        "goal":                          goal,
        "target_program_or_scholarship": target_program_or_scholarship.strip(),
        "deadline":                      deadline,
        "status":                        "active",
        "assigned_volunteer":            assigned_volunteer.strip(),
        "summary":                       summary.strip(),
        "contact_number":                contact_number.strip(),
        "age":                           age.strip(),
        "education_level":               education_level.strip(),
        "created_at":                    datetime.now().isoformat(),
        "updated_at":                    datetime.now().isoformat(),
        "closed_at":                     None,
    }
    cases.append(case)
    _save(CASES_FILE, cases)
    return case


def get_case(case_id: str) -> Optional[dict]:
    return next((c for c in _load(CASES_FILE) if c["case_id"] == case_id), None)


def list_cases(status: Optional[str] = None, volunteer: Optional[str] = None,
               goal: Optional[str] = None, location: Optional[str] = None) -> list:
    cases = _load(CASES_FILE)
    if status:
        cases = [c for c in cases if c["status"] == status]
    if volunteer:
        cases = [c for c in cases if c.get("assigned_volunteer") == volunteer]
    if goal:
        cases = [c for c in cases if c.get("goal") == goal]
    if location:
        loc = location.lower()
        cases = [c for c in cases if loc in c.get("location", "").lower()]
    return sorted(cases, key=lambda c: c.get("created_at", ""), reverse=True)


def search_cases(query: str) -> list:
    """Keyword search across all text fields."""
    if not query:
        return list_cases()
    q = query.lower()
    return [
        c for c in _load(CASES_FILE)
        if q in c.get("student_name", "").lower()
        or q in c.get("location", "").lower()
        or q in c.get("goal", "").lower()
        or q in c.get("target_program_or_scholarship", "").lower()
        or q in c.get("assigned_volunteer", "").lower()
        or q in c.get("summary", "").lower()
        or q in c.get("case_id", "").lower()
        or q in c.get("contact_number", "").lower()
    ]


def update_case(case_id: str, **fields) -> Optional[dict]:
    """Update any editable case fields."""
    allowed = {"student_name", "location", "goal", "target_program_or_scholarship",
               "deadline", "assigned_volunteer", "summary",
               "contact_number", "age", "education_level"}
    cases = _load(CASES_FILE)
    for c in cases:
        if c["case_id"] == case_id:
            for k, v in fields.items():
                if k in allowed:
                    c[k] = v
            c["updated_at"] = datetime.now().isoformat()
            _save(CASES_FILE, cases)
            return c
    return None


def update_case_status(case_id: str, status: str) -> Optional[dict]:
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}")
    cases = _load(CASES_FILE)
    for c in cases:
        if c["case_id"] == case_id:
            c["status"]     = status
            c["updated_at"] = datetime.now().isoformat()
            c["closed_at"]  = datetime.now().isoformat() if status == "closed" else None
            _save(CASES_FILE, cases)
            return c
    return None


def purge_case(case_id: str):
    """Hard delete: case + all documents + all follow-ups."""
    _save(CASES_FILE,     [c for c in _load(CASES_FILE)     if c["case_id"] != case_id])
    _save(DOCUMENTS_FILE, [d for d in _load(DOCUMENTS_FILE) if d["case_id"] != case_id])
    _save(FOLLOWUPS_FILE, [f for f in _load(FOLLOWUPS_FILE) if f["case_id"] != case_id])


def list_volunteers() -> list:
    cases = _load(CASES_FILE)
    names = {c.get("assigned_volunteer", "").strip() for c in cases}
    return sorted(n for n in names if n)


def get_stats() -> dict:
    cases     = _load(CASES_FILE)
    docs      = _load(DOCUMENTS_FILE)
    followups = _load(FOLLOWUPS_FILE)
    active    = [c for c in cases if c["status"] == "active"]
    closed    = [c for c in cases if c["status"] == "closed"]
    by_goal   = {}
    for c in cases:
        g = c.get("goal", "Other")
        by_goal[g] = by_goal.get(g, 0) + 1
    by_volunteer = {}
    for c in active:
        v = c.get("assigned_volunteer", "Unassigned")
        by_volunteer[v] = by_volunteer.get(v, 0) + 1
    by_location = {}
    for c in cases:
        loc = c.get("location", "Unknown")
        by_location[loc] = by_location.get(loc, 0) + 1
    missing_docs = sum(1 for d in docs if d["status"] == "missing")
    return {
        "total": len(cases), "active": len(active), "closed": len(closed),
        "total_followups": len(followups), "total_docs": len(docs),
        "missing_docs": missing_docs, "by_goal": by_goal,
        "by_volunteer": by_volunteer, "by_location": by_location,
    }


# ── Document ──────────────────────────────────────────────────────────────────

def add_document(case_id: str, doc_name: str, status: str, notes: str = "") -> dict:
    if status not in VALID_DOC_STATUSES:
        raise ValueError(f"status must be one of {VALID_DOC_STATUSES}")
    docs = _load(DOCUMENTS_FILE)
    doc = {
        "doc_id":     str(uuid.uuid4())[:8],
        "case_id":    case_id,
        "doc_name":   doc_name,
        "status":     status,
        "notes":      notes,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    docs.append(doc)
    _save(DOCUMENTS_FILE, docs)
    return doc


def list_documents(case_id: str) -> list:
    return [d for d in _load(DOCUMENTS_FILE) if d["case_id"] == case_id]


def update_document(doc_id: str, status: Optional[str] = None,
                    notes: Optional[str] = None) -> Optional[dict]:
    if status and status not in VALID_DOC_STATUSES:
        raise ValueError(f"status must be one of {VALID_DOC_STATUSES}")
    docs = _load(DOCUMENTS_FILE)
    for d in docs:
        if d["doc_id"] == doc_id:
            if status is not None:
                d["status"] = status
            if notes is not None:
                d["notes"] = notes
            d["updated_at"] = datetime.now().isoformat()
            _save(DOCUMENTS_FILE, docs)
            return d
    return None


def delete_document(doc_id: str):
    _save(DOCUMENTS_FILE, [d for d in _load(DOCUMENTS_FILE) if d["doc_id"] != doc_id])


# ── FollowUp ──────────────────────────────────────────────────────────────────

def add_followup(case_id: str, worker_name: str, note_text: str,
                 blockers: str = "", next_step: str = "",
                 next_followup_date: Optional[str] = None,
                 followup_type: str = "call") -> dict:
    followups = _load(FOLLOWUPS_FILE)
    followup = {
        "followup_id":        str(uuid.uuid4())[:8],
        "case_id":            case_id,
        "date":               datetime.now().isoformat(),
        "worker_name":        worker_name,
        "note_text":          note_text,
        "blockers":           blockers,
        "next_step":          next_step,
        "next_followup_date": next_followup_date,
        "followup_type":      followup_type,
    }
    followups.append(followup)
    _save(FOLLOWUPS_FILE, followups)
    return followup


def list_followups(case_id: Optional[str] = None) -> list:
    followups = _load(FOLLOWUPS_FILE)
    if case_id:
        followups = [f for f in followups if f["case_id"] == case_id]
    return sorted(followups, key=lambda f: f["date"], reverse=True)


def delete_followup(followup_id: str):
    _save(FOLLOWUPS_FILE,
          [f for f in _load(FOLLOWUPS_FILE) if f["followup_id"] != followup_id])


def last_followup_date(case_id: str) -> Optional[date]:
    followups = list_followups(case_id)
    if not followups:
        return None
    return datetime.fromisoformat(followups[0]["date"]).date()


def all_followups_with_case() -> list:
    """All follow-ups joined with student name — for activity feed."""
    followups = _load(FOLLOWUPS_FILE)
    cases     = {c["case_id"]: c for c in _load(CASES_FILE)}
    result = []
    for f in followups:
        case = cases.get(f["case_id"], {})
        result.append({**f, "student_name": case.get("student_name", "Unknown")})
    return sorted(result, key=lambda f: f["date"], reverse=True)
