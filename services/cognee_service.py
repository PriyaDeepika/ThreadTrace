"""
cognee_service.py — ThreadTrace AI Memory Layer

All Cognee Cloud integration lives here. Uses COGNEE_BASE_URL + COGNEE_API_KEY.
Cognee is used throughout ThreadTrace, not just in the Ask page:
  - remember()      : every follow-up note, case creation context, document updates
  - recall()        : case summaries, cross-case queries, contextual search
  - forget()        : case purge (GDPR-style hard delete)
  - improve()       : memory enrichment after bulk ingestion

Cognee integrations across the app:
  1. Add Follow-Up       → remember_followup()
  2. Add Case            → remember_case_context()
  3. Ask ThreadTrace      → recall_case(), recall_across_cases()
  4. Case Detail sidebar → summarize_case(), suggest_next_action()
  5. Search page         → semantic_search()
  6. Reports page        → generate_insights()
  7. Close/Purge         → forget_case()
  8. Dashboard           → recall_urgent_context()
"""

import os
import asyncio
import cognee
from dotenv import load_dotenv

load_dotenv()

_connected = False


# ── connection ────────────────────────────────────────────────────────────────

async def _ensure_connected():
    global _connected
    if _connected:
        return
    base_url = os.environ.get("COGNEE_BASE_URL", "").strip()
    api_key  = os.environ.get("COGNEE_API_KEY", "").strip()
    if not base_url or not api_key:
        raise RuntimeError(
            "COGNEE_BASE_URL and COGNEE_API_KEY must be set in your .env file.\n"
            "Sign up at Cognee Cloud, claim credit with COGNEE-35, then add:\n"
            "  COGNEE_BASE_URL=https://your-tenant.aws.cognee.ai\n"
            "  COGNEE_API_KEY=ck_..."
        )
    await cognee.serve(url=base_url, api_key=api_key)
    _connected = True


def cognee_available() -> bool:
    """Check if Cognee credentials are configured (without connecting)."""
    base_url = os.environ.get("COGNEE_BASE_URL", "").strip()
    api_key  = os.environ.get("COGNEE_API_KEY", "").strip()
    return bool(base_url and api_key)


def _dataset(case_id: str) -> str:
    """One Cognee dataset per case — enables clean per-case forget()."""
    return f"case_{case_id}"


# ── remember ──────────────────────────────────────────────────────────────────

async def _remember_text(text: str, dataset_name: str) -> None:
    await _ensure_connected()
    await cognee.remember(text, dataset_name=dataset_name)


def remember_followup(case_id: str, student_name: str, worker_name: str,
                      note_text: str, blockers: str = "", next_step: str = "",
                      followup_type: str = "call") -> None:
    """
    Called on every Add Follow-Up submission.
    Ingests the full context of a follow-up into Cognee as one memory unit.
    """
    text = (
        f"[FOLLOW-UP] Case: {student_name} (case_id: {case_id})\n"
        f"Type: {followup_type}\n"
        f"Worker: {worker_name}\n"
        f"Note: {note_text}\n"
    )
    if blockers:
        text += f"Blocker: {blockers}\n"
    if next_step:
        text += f"Next step promised: {next_step}\n"
    run_async(_remember_text(text, _dataset(case_id)))


def remember_case_context(case_id: str, student_name: str, location: str,
                          goal: str, program: str, deadline: str,
                          volunteer: str, summary: str = "") -> None:
    """
    Called on case creation. Seeds Cognee with the case's initial context
    so recall() has a baseline even before any follow-ups are added.
    """
    text = (
        f"[CASE CREATED] Student: {student_name} (case_id: {case_id})\n"
        f"Location: {location}\n"
        f"Goal: {goal}\n"
        f"Target program / scholarship: {program}\n"
        f"Deadline: {deadline}\n"
        f"Assigned volunteer: {volunteer}\n"
    )
    if summary:
        text += f"Initial notes: {summary}\n"
    run_async(_remember_text(text, _dataset(case_id)))


def remember_document_update(case_id: str, student_name: str,
                             doc_name: str, status: str, notes: str = "") -> None:
    """
    Called when a document status is added or updated.
    Keeps Cognee's memory current with document progress.
    """
    text = (
        f"[DOCUMENT UPDATE] Case: {student_name} (case_id: {case_id})\n"
        f"Document: {doc_name}\n"
        f"Status changed to: {status}\n"
    )
    if notes:
        text += f"Notes: {notes}\n"
    run_async(_remember_text(text, _dataset(case_id)))


# ── recall ────────────────────────────────────────────────────────────────────

async def _recall(question: str, datasets) -> str:
    await _ensure_connected()

    # If a single dataset name is passed, convert it to a list
    if isinstance(datasets, str):
        datasets = [datasets]

    results = await cognee.recall(
        question,
        datasets=datasets
    )

    return _fmt(results)

def recall_case(case_id: str, question: str) -> str:
    """Free-form question scoped to one case's memory."""
    return run_async(_recall(question, _dataset(case_id)))


def recall_across_cases(question: str, case_ids: list) -> str:
    """Cross-case question over multiple datasets."""
    datasets = [_dataset(cid) for cid in case_ids]
    return run_async(_recall(question, datasets))


def summarize_case(case_id: str, student_name: str) -> str:
    """
    Generates a concise AI summary of everything Cognee knows about this case.
    Used in Case Detail page sidebar.
    """
    q = (
        f"Give a concise 3-5 bullet summary of {student_name}'s case. "
        f"Include: current status, what's been done, key blockers, "
        f"missing documents, and the most important next action."
    )
    return run_async(_recall(q, _dataset(case_id)))


def suggest_next_action(case_id: str, student_name: str) -> str:
    """
    AI-suggested next action based on case memory.
    Used in Case Detail page as an actionable recommendation.
    """
    q = (
        f"Based on the history of {student_name}'s case, what is the single most "
        f"important next action the volunteer should take? Be specific and concise."
    )
    return run_async(_recall(q, _dataset(case_id)))


def recall_urgent_context(case_ids: list, cases: list = None) -> str:
    """
    Dashboard use: AI summary of what needs attention across all active cases.

    `cases` is the list of active case dicts — if provided, the prompt is
    enriched with real deadline/follow-up data so priority is accurate.
    """
    if not case_ids:
        return "No active cases to summarize."

    import json as _json
    from datetime import date as _date, datetime as _datetime
    from services import storage_service as _storage

    today = _date.today()

    # Build a compact fact-table so the LLM knows the real deadlines
    case_facts = []
    for cid in case_ids:
        case = next((c for c in (cases or []) if c["case_id"] == cid), None)
        if case is None:
            # Fall back to loading from storage
            case = _storage.get_case(cid)
        if not case:
            continue
        try:
            dl = _datetime.fromisoformat(case["deadline"]).date()
            days_left = (dl - today).days
        except Exception:
            days_left = 999

        followups = _storage.list_followups(cid)
        if followups:
            last_fup = _datetime.fromisoformat(followups[0]["date"]).date()
            days_since = (today - last_fup).days
        else:
            days_since = None

        missing_docs = sum(
            1 for d in _storage.list_documents(cid) if d["status"] == "missing"
        )

        case_facts.append({
            "case_id":        cid,
            "student":        case["student_name"],
            "deadline":       case["deadline"][:10],
            "days_until_dl":  days_left,
            "days_no_followup": days_since,
            "missing_docs":   missing_docs,
        })

    facts_str = _json.dumps(case_facts, indent=2)

    q = f"""You are an NGO case management assistant. Today is {today.isoformat()}.

CASE FACTS (authoritative — use these for deadline and priority decisions):
{facts_str}

Use the Cognee memory to add context (blockers, latest notes, what happened).
Then assign priority to each case using EXACTLY these rules:

HIGH: days_until_dl <= 3, OR missing_docs > 0 AND days_until_dl <= 7, OR days_no_followup > 14.
MEDIUM: days_until_dl between 4 and 7 (inclusive), OR days_no_followup between 8 and 14.
LOW: days_until_dl > 7 AND days_no_followup < 8.

Return ONLY cases that need attention (skip LOW cases with no blockers).
Return between 0 and 5 students. Never repeat the same student.
Sort by priority: HIGH → MEDIUM → LOW.
Keep issue and action to 1 sentence each.

Return ONLY valid JSON. Do not include markdown, explanations, or code blocks.
The response MUST begin with '[' and end with ']'.

Return exactly this format:
[
  {{
    "priority": "HIGH",
    "student": "Student Name",
    "case_id": "case_id",
    "deadline": "YYYY-MM-DD",
    "issue": "Short description of the problem",
    "action": "Specific next action for the volunteer"
  }}
]
"""
    datasets = [_dataset(cid) for cid in case_ids]
    return run_async(_recall(q, datasets))



def semantic_search(query: str, case_ids: list) -> str:
    """
    Semantic search across all case memories.
    Used in the Search page for AI-powered contextual search beyond keyword matching.
    """
    if not case_ids:
        return "No cases in memory to search."
    q = f"Find cases and context related to: {query}"
    datasets = [_dataset(cid) for cid in case_ids]
    return run_async(_recall(q, datasets))


def generate_insights(case_ids: list) -> str:
    """
    Reports page: AI-generated insights across the whole caseload.
    Surfaces patterns, common blockers, and recommendations.
    """
    if not case_ids:
        return "No cases to analyze."
    q = (
        "Analyze all cases and provide: "
        "1) The most common blockers across cases, "
        "2) Which cases need the most urgent attention, "
        "3) Patterns in missing documents, "
        "4) One concrete recommendation to improve case outcomes overall."
    )
    datasets = [_dataset(cid) for cid in case_ids]
    return run_async(_recall(q, datasets))


# ── forget ────────────────────────────────────────────────────────────────────

async def _forget(case_id: str) -> None:
    await _ensure_connected()
    await cognee.forget(dataset=_dataset(case_id))


def forget_case(case_id: str) -> None:
    """
    Hard delete from Cognee. Always pair with storage_service.purge_case().
    This is the real forget() demo moment — not just a status flag.
    """
    run_async(_forget(case_id))


# ── improve ───────────────────────────────────────────────────────────────────

async def _improve(case_id: str) -> None:
    await _ensure_connected()
    if hasattr(cognee, "memify"):
        await cognee.memify(dataset=_dataset(case_id))
    elif hasattr(cognee, "improve"):
        await cognee.improve(dataset=_dataset(case_id))


def improve_case_memory(case_id: str) -> None:
    """
    Re-rank and prune stale memory for a case.
    Available as a button on Case Detail page after many follow-ups.
    """
    run_async(_improve(case_id))


# ── formatting ────────────────────────────────────────────────────────────────

# def _fmt(results) -> str:
#     if results is None:
#         return "No memory found for this query yet. Add follow-up notes to build case memory."
#     if isinstance(results, str):
#         return results.strip()
#     if isinstance(results, list):
#         parts = []
#         for r in results:
#             if isinstance(r, dict):
#                 parts.append(r.get("text", str(r)).strip())
#             else:
#                 parts.append(str(r).strip())
#         return "\n\n".join(p for p in parts if p) or "No results found."
#     return str(results).strip()

import json

def _fmt(results) -> str:
    if results is None:
        return "[]"

    if isinstance(results, str):
        return results.strip()

    def _serializer(obj):
        # Pydantic v2 models (Cognee RecallResponse objects)
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # Pydantic v1 models
        if hasattr(obj, "dict"):
            return obj.dict()
        return str(obj)

    if isinstance(results, list):
        return json.dumps(results, default=_serializer)

    return json.dumps(results, default=_serializer)

# ── async runner ──────────────────────────────────────────────────────────────

import threading
import concurrent.futures

# ── Persistent event loop in a dedicated background thread ────────────────────
# On Windows + Python 3.12, asyncio.run() closes the loop after each call.
# aiohttp (used by Cognee Cloud client) holds references to the loop and
# raises "Event loop is closed" when asyncio.run() is called again.
# Fix: one persistent loop running in a daemon thread, reused for all calls.

_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None
_loop_lock = threading.Lock()


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop, _loop_thread
    with _loop_lock:
        if _loop is None or _loop.is_closed():
            _loop = asyncio.new_event_loop()
            _loop_thread = threading.Thread(
                target=_loop.run_forever, daemon=True, name="cognee-event-loop"
            )
            _loop_thread.start()
    return _loop


def run_async(coro):
    """
    Run an async Cognee coroutine from synchronous Streamlit code.
    Uses a single persistent event loop in a daemon thread — safe on
    Windows Python 3.12 where asyncio.run() closes the loop after each call.
    """
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=120)  # 2-minute timeout
