"""
query_service.py

Derived/computed logic that sits on top of storage_service's raw records.
Kept separate from storage_service so "what counts as urgent" is a single,
easy-to-change decision in one place, not scattered across UI pages.

Decision (per architecture notes): urgency is COMPUTED, not a manually-set
status. A case is urgent if:
  - its deadline is within URGENT_WINDOW_DAYS, OR
  - it hasn't had a follow-up in OVERDUE_FOLLOWUP_DAYS
This means the dashboard can never silently lie because a volunteer forgot
to flag something — it's always recalculated from real dates.
"""

from datetime import date, datetime
from services import storage_service as storage

URGENT_WINDOW_DAYS = 5
OVERDUE_FOLLOWUP_DAYS = 10


def _days_until(deadline_str: str) -> int:
    deadline = datetime.fromisoformat(deadline_str).date()
    return (deadline - date.today()).days


def _days_since_last_followup(case_id: str) -> int | None:
    last = storage.last_followup_date(case_id)
    if last is None:
        return None
    return (date.today() - last).days


def is_urgent(case: dict) -> bool:
    if case["status"] != "active":
        return False
    if _days_until(case["deadline"]) <= URGENT_WINDOW_DAYS:
        return True
    days_since = _days_since_last_followup(case["case_id"])
    if days_since is not None and days_since >= OVERDUE_FOLLOWUP_DAYS:
        return True
    return False


def is_overdue_for_followup(case: dict) -> bool:
    days_since = _days_since_last_followup(case["case_id"])
    if days_since is None:
        # never followed up at all — treat as overdue
        return True
    return days_since >= OVERDUE_FOLLOWUP_DAYS


def missing_documents_count(case_id: str) -> int:
    docs = storage.list_documents(case_id)
    return sum(1 for d in docs if d["status"] == "missing")


def dashboard_summary() -> dict:
    """Powers the four dashboard cards: active, urgent, missing docs, overdue."""
    active_cases = storage.list_cases(status="active")
    urgent = [c for c in active_cases if is_urgent(c)]
    overdue = [c for c in active_cases if is_overdue_for_followup(c)]
    total_missing_docs = sum(missing_documents_count(c["case_id"]) for c in active_cases)

    return {
        "active_count": len(active_cases),
        "urgent_cases": urgent,
        "overdue_cases": overdue,
        "missing_docs_total": total_missing_docs,
    }


def cases_with_deadline_this_week() -> list[dict]:
    active_cases = storage.list_cases(status="active")
    return [c for c in active_cases if 0 <= _days_until(c["deadline"]) <= 7]
