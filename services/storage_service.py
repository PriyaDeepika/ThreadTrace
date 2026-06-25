"""
storage_service.py

Handles ALL structured/local data: StudentCase and Document records.
This is deliberately NOT sent to Cognee — Cognee only stores the messy
unstructured text (FollowUp notes). See cognee_service.py for that.

Uses flat JSON files for MVP simplicity. Swap for SQLite later if needed —
the function signatures below won't need to change.
"""

import json
import os
import uuid
from datetime import datetime, date
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CASES_FILE = os.path.join(DATA_DIR, "cases.json")
DOCUMENTS_FILE = os.path.join(DATA_DIR, "documents.json")
FOLLOWUPS_FILE = os.path.join(DATA_DIR, "followups.json")

VALID_STATUSES = ["active", "closed"]  # "urgent" is computed, not stored — see query_service.py
VALID_DOC_STATUSES = ["submitted", "missing", "pending_verification"]


# ---------- low-level file helpers ----------

def _ensure_file(path: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)


def _load(path: str) -> list:
    _ensure_file(path)
    with open(path, "r") as f:
        return json.load(f)


def _save(path: str, records: list):
    _ensure_file(path)
    with open(path, "w") as f:
        json.dump(records, f, indent=2, default=str)


# ---------- StudentCase ----------

def create_case(
    student_name: str,
    location: str,
    goal: str,
    target_program_or_scholarship: str,
    deadline: str,            # ISO format "YYYY-MM-DD"
    assigned_volunteer: str,
    summary: str = "",
) -> dict:
    """Creates a new StudentCase record. Returns the created case dict."""
    cases = _load(CASES_FILE)
    case = {
        "case_id": str(uuid.uuid4())[:8],
        "student_name": student_name,
        "location": location,
        "goal": goal,
        "target_program_or_scholarship": target_program_or_scholarship,
        "deadline": deadline,
        "status": "active",
        "assigned_volunteer": assigned_volunteer,
        "summary": summary,
        "created_at": datetime.now().isoformat(),
    }
    cases.append(case)
    _save(CASES_FILE, cases)
    return case


def get_case(case_id: str) -> Optional[dict]:
    cases = _load(CASES_FILE)
    return next((c for c in cases if c["case_id"] == case_id), None)


def list_cases(status: Optional[str] = None) -> list:
    cases = _load(CASES_FILE)
    if status:
        cases = [c for c in cases if c["status"] == status]
    return cases


def update_case_status(case_id: str, status: str) -> Optional[dict]:
    """Soft status change only (active/closed). Use purge_case() for hard delete."""
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}")
    cases = _load(CASES_FILE)
    for c in cases:
        if c["case_id"] == case_id:
            c["status"] = status
            c["closed_at"] = datetime.now().isoformat() if status == "closed" else None
            _save(CASES_FILE, cases)
            return c
    return None


def purge_case(case_id: str):
    """
    Hard delete: removes the case and all its documents/followups from
    local storage. Pair this with cognee_service.forget_case() to also
    purge the case from Cognee's memory. This is the real forget() demo —
    distinct from update_case_status('closed'), which just archives.
    """
    cases = [c for c in _load(CASES_FILE) if c["case_id"] != case_id]
    _save(CASES_FILE, cases)

    docs = [d for d in _load(DOCUMENTS_FILE) if d["case_id"] != case_id]
    _save(DOCUMENTS_FILE, docs)

    followups = [f for f in _load(FOLLOWUPS_FILE) if f["case_id"] != case_id]
    _save(FOLLOWUPS_FILE, followups)


# ---------- Document ----------

def add_document(case_id: str, doc_name: str, status: str, notes: str = "") -> dict:
    if status not in VALID_DOC_STATUSES:
        raise ValueError(f"status must be one of {VALID_DOC_STATUSES}")
    docs = _load(DOCUMENTS_FILE)
    doc = {
        "doc_id": str(uuid.uuid4())[:8],
        "case_id": case_id,
        "doc_name": doc_name,
        "status": status,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }
    docs.append(doc)
    _save(DOCUMENTS_FILE, docs)
    return doc


def list_documents(case_id: str) -> list:
    return [d for d in _load(DOCUMENTS_FILE) if d["case_id"] == case_id]


def update_document_status(doc_id: str, status: str) -> Optional[dict]:
    if status not in VALID_DOC_STATUSES:
        raise ValueError(f"status must be one of {VALID_DOC_STATUSES}")
    docs = _load(DOCUMENTS_FILE)
    for d in docs:
        if d["doc_id"] == doc_id:
            d["status"] = status
            _save(DOCUMENTS_FILE, docs)
            return d
    return None


# ---------- FollowUp (local copy, for dashboard filtering) ----------
# NOTE: the note_text ALSO gets sent to cognee_service.remember_followup().
# This local copy exists so the dashboard can filter/sort without round-tripping
# to Cognee for every page load.

def add_followup(
    case_id: str,
    worker_name: str,
    note_text: str,
    blockers: str = "",
    next_step: str = "",
    next_followup_date: Optional[str] = None,
) -> dict:
    followups = _load(FOLLOWUPS_FILE)
    followup = {
        "followup_id": str(uuid.uuid4())[:8],
        "case_id": case_id,
        "date": datetime.now().isoformat(),
        "worker_name": worker_name,
        "note_text": note_text,
        "blockers": blockers,
        "next_step": next_step,
        "next_followup_date": next_followup_date,
    }
    followups.append(followup)
    _save(FOLLOWUPS_FILE, followups)
    return followup


def list_followups(case_id: Optional[str] = None) -> list:
    followups = _load(FOLLOWUPS_FILE)
    if case_id:
        followups = [f for f in followups if f["case_id"] == case_id]
    return sorted(followups, key=lambda f: f["date"], reverse=True)


def last_followup_date(case_id: str) -> Optional[date]:
    followups = list_followups(case_id)
    if not followups:
        return None
    return datetime.fromisoformat(followups[0]["date"]).date()
