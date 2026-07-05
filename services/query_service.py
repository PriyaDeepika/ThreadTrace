"""
query_service.py — Computed/derived logic for ThreadTrace dashboards and reports.

Urgency, overdue, workload, and report generation.
Never import Streamlit here — this is pure logic, usable from any page.
"""

import csv
import io
from datetime import date, datetime, timedelta
from typing import Optional
from services import storage_service as storage

URGENT_WINDOW_DAYS    = 5
OVERDUE_FOLLOWUP_DAYS = 10


# ── date helpers ──────────────────────────────────────────────────────────────

def days_until(deadline_str: str) -> int:
    try:
        return (datetime.fromisoformat(deadline_str).date() - date.today()).days
    except Exception:
        return 999


def days_since_followup(case_id: str) -> Optional[int]:
    last = storage.last_followup_date(case_id)
    if last is None:
        return None
    return (date.today() - last).days


# ── urgency ───────────────────────────────────────────────────────────────────

def is_urgent(case: dict) -> bool:
    if case["status"] != "active":
        return False
    if days_until(case["deadline"]) <= URGENT_WINDOW_DAYS:
        return True
    ds = days_since_followup(case["case_id"])
    return ds is not None and ds >= OVERDUE_FOLLOWUP_DAYS


def is_overdue_for_followup(case: dict) -> bool:
    ds = days_since_followup(case["case_id"])
    return ds is None or ds >= OVERDUE_FOLLOWUP_DAYS


"""def urgency_label(case: dict) -> str:
    if case["status"] == "closed":
        return "✅ Closed"
    d = days_until(case["deadline"])
    if d < 0:
        return f"⛔ {abs(d)}d overdue"
    if d <= URGENT_WINDOW_DAYS:
        return f"🔴 {d}d left"
    ds = days_since_followup(case["case_id"])
    if ds is None:
        return "🟡 Never followed up"
    if ds >= OVERDUE_FOLLOWUP_DAYS:
        return f"🟡 {ds}d no follow-up"
    return "🟢 On track"
"""

def urgency_label(case: dict) -> str:
    """
    Returns a user-friendly urgency label for dashboard cards.
    Priority order:
    Overdue > Critical > High > Medium > Normal > Closed
    """

    if case["status"] == "closed":
        return "✅ Closed"

    days_left = days_until(case["deadline"])
    followup_gap = days_since_followup(case["case_id"])

    # Deadline already passed
    if days_left < 0:
        return f"⛔ Overdue ({abs(days_left)}d)"

    # Deadline is today or tomorrow
    if days_left <= 1:
        return f"🔴 Critical ({days_left}d left)"

    # Deadline within next 3 days
    if days_left <= 3:
        return f"🔴 High Priority ({days_left}d left)"

    # Deadline within a week
    if days_left <= 7:
        return f"🟡 Upcoming ({days_left}d left)"

    # No follow-up ever
    if followup_gap is None:
        return "🟠 Needs First Follow-up"

    # Long time since follow-up
    if followup_gap >= OVERDUE_FOLLOWUP_DAYS:
        return f"🟠 Follow-up Overdue ({followup_gap}d)"

    # Everything looks fine
    return "🟢 On Track"


def missing_docs_count(case_id: str) -> int:
    return sum(1 for d in storage.list_documents(case_id) if d["status"] == "missing")


# ── dashboard ─────────────────────────────────────────────────────────────────

def dashboard_summary() -> dict:
    active  = storage.list_cases(status="active")
    closed  = storage.list_cases(status="closed")
    urgent  = [c for c in active if is_urgent(c)]
    overdue = [c for c in active if is_overdue_for_followup(c)]
    missing = sum(missing_docs_count(c["case_id"]) for c in active)
    return {
        "active_count":  len(active),
        "closed_count":  len(closed),
        "urgent_cases":  urgent,
        "overdue_cases": overdue,
        "missing_docs":  missing,
    }
    # kept the old key "missing_docs_total" as alias below for backwards compat
dashboard_summary_compat = dashboard_summary  # old key was missing_docs_total


def cases_with_deadline_this_week() -> list:
    return [c for c in storage.list_cases(status="active")
            if 0 <= days_until(c["deadline"]) <= 7]


def cases_deadline_overdue() -> list:
    return [c for c in storage.list_cases(status="active")
            if days_until(c["deadline"]) < 0]


def recent_activity(limit: int = 15) -> list:
    return storage.all_followups_with_case()[:limit]


# ── volunteer workload ────────────────────────────────────────────────────────

def volunteer_workload() -> list:
    active   = storage.list_cases(status="active")
    workload = {}
    for c in active:
        v = c.get("assigned_volunteer", "Unassigned")
        if v not in workload:
            workload[v] = {"volunteer": v, "cases": 0, "urgent": 0, "overdue": 0}
        workload[v]["cases"] += 1
        if is_urgent(c):
            workload[v]["urgent"] += 1
        if is_overdue_for_followup(c):
            workload[v]["overdue"] += 1
    return sorted(workload.values(), key=lambda x: x["cases"], reverse=True)


# ── reports ───────────────────────────────────────────────────────────────────

def generate_report() -> dict:
    stats    = storage.get_stats()
    all_fups = storage.list_followups()

    fup_counts = {}
    for f in all_fups:
        fup_counts[f["case_id"]] = fup_counts.get(f["case_id"], 0) + 1
    avg_fups = round(sum(fup_counts.values()) / len(fup_counts), 1) if fup_counts else 0

    activity_by_day = {}
    cutoff = date.today() - timedelta(days=14)
    for f in all_fups:
        try:
            d = datetime.fromisoformat(f["date"]).date()
        except Exception:
            continue
        if d >= cutoff:
            key = d.isoformat()
            activity_by_day[key] = activity_by_day.get(key, 0) + 1

    return {
        **stats,
        "avg_followups_per_case":  avg_fups,
        "overdue_deadline_count":  len(cases_deadline_overdue()),
        "thisweek_deadline_count": len(cases_with_deadline_this_week()),
        "activity_by_day":         activity_by_day,
        "volunteer_workload":      volunteer_workload(),
    }


def export_cases_csv() -> str:
    cases = storage.list_cases()
    if not cases:
        return ""
    fields = ["case_id", "student_name", "location", "goal",
              "target_program_or_scholarship", "deadline", "status",
              "assigned_volunteer", "contact_number", "age",
              "education_level", "summary", "created_at", "closed_at"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(cases)
    return buf.getvalue()


def export_followups_csv() -> str:
    followups = storage.all_followups_with_case()
    if not followups:
        return ""
    fields = ["followup_id", "case_id", "student_name", "date",
              "worker_name", "followup_type", "note_text",
              "blockers", "next_step", "next_followup_date"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(followups)
    return buf.getvalue()
