"""
cognee_service.py

Thin wrapper around Cognee's memory API. Every function here maps 1:1
to a line in your demo script — keep it that way, don't let this file
grow generic helper soup.

Design decisions (see architecture notes):
- Only FollowUp.note_text gets ingested into Cognee. StudentCase and
  Document are structured fields with no "messy text" worth a knowledge
  graph — they live in storage_service.py / local JSON only.
- Each follow-up is remembered as its OWN unit, tagged with case_id as
  metadata. This is what lets recall() do cross-followup reasoning
  ("summarize Ravi's case") without you writing aggregation logic by hand.
- dataset_name is per-case ("case_<case_id>") so forget_case() can cleanly
  delete one case's memory without touching others.

Auth: set COGNEE_SERVICE_URL and COGNEE_API_KEY in your .env (see
.env.example). This module reads them via os.environ — never hardcode.
"""

import os
import asyncio
import cognee
from dotenv import load_dotenv

load_dotenv()

_connected = False


async def _ensure_connected():
    """
    Connects to Cognee Cloud once per process. Cheap to call repeatedly —
    Streamlit reruns the script on every interaction, so every public
    function below calls this first.
    """
    global _connected
    if _connected:
        return
    url = os.environ.get("COGNEE_SERVICE_URL")
    api_key = os.environ.get("COGNEE_API_KEY")
    if not url or not api_key:
        raise RuntimeError(
            "COGNEE_SERVICE_URL / COGNEE_API_KEY not set. Copy .env.example to "
            ".env and fill in your Cognee Cloud credentials."
        )
    await cognee.serve(url=url, api_key=api_key)
    _connected = True


def _dataset_for(case_id: str) -> str:
    """One dataset per case — this is what makes forget() a clean per-case purge."""
    return f"case_{case_id}"


# ---------- remember() ----------

async def remember_followup(case_id: str, student_name: str, worker_name: str,
                              note_text: str, blockers: str = "", next_step: str = "") -> None:
    """
    Ingests a single follow-up note into Cognee, scoped to this case's dataset.
    Called right after storage_service.add_followup() — same user action,
    two writes (local structured copy + Cognee memory).
    """
    await _ensure_connected()

    # Compose a single text blob so context (who/what/blockers/next step)
    # travels together as one memory unit rather than getting split oddly.
    text = (
        f"Case: {student_name} (case_id: {case_id})\n"
        f"Worker: {worker_name}\n"
        f"Note: {note_text}\n"
    )
    if blockers:
        text += f"Blocker: {blockers}\n"
    if next_step:
        text += f"Next step: {next_step}\n"

    await cognee.remember(text, dataset_name=_dataset_for(case_id))


# ---------- recall() ----------

async def recall_case(case_id: str, question: str) -> str:
    """
    Ask a question scoped to ONE case's memory.
    e.g. "What's pending for Ravi?", "Summarize this case."
    """
    await _ensure_connected()
    results = await cognee.recall(question, dataset_name=_dataset_for(case_id))
    return _format_recall(results)


async def recall_across_cases(question: str, case_ids: list[str]) -> str:
    """
    Ask a question that spans MULTIPLE cases.
    e.g. "Who hasn't been followed up in 10 days?" across the whole caseload.
    Cognee's dataset_name accepts a list for cross-dataset queries.
    """
    await _ensure_connected()
    datasets = [_dataset_for(cid) for cid in case_ids]
    results = await cognee.recall(question, dataset_name=datasets)
    return _format_recall(results)


def _format_recall(results) -> str:
    """Normalizes Cognee's recall() response into a plain string for display."""
    if results is None:
        return "No memory found for this query yet."
    if isinstance(results, str):
        return results
    # results may be a list of result objects / dicts depending on SDK version
    if isinstance(results, list):
        return "\n".join(str(r) for r in results)
    return str(results)


# ---------- forget() ----------

async def forget_case(case_id: str) -> None:
    """
    Hard delete: purges this case's entire dataset from Cognee's memory.
    Call this together with storage_service.purge_case() — never alone,
    or you'll have local records pointing at memory that no longer exists.
    """
    await _ensure_connected()
    await cognee.forget(dataset_name=_dataset_for(case_id))


# ---------- improve() / memify() ----------

async def improve_case_memory(case_id: str) -> None:
    """
    Stretch goal, not required for MVP demo. Runs Cognee's improve()/memify()
    over a case's dataset to compress/re-rank memory after many follow-ups
    pile up. Wire this to a button on the case detail page if you have time
    left after the core 5 features work.
    """
    await _ensure_connected()
    await cognee.memify(dataset_name=_dataset_for(case_id))


# ---------- sync helpers for Streamlit ----------
# Streamlit callbacks are synchronous; these let pages call async Cognee
# functions without manual asyncio boilerplate scattered everywhere.

def run_async(coro):
    """Run an async Cognee call from a synchronous Streamlit page."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
