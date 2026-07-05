import streamlit as st
from services import storage_service as storage
from services import cognee_service as cognee_svc
from services import query_service as query
from utils.helpers import (
    cognee_status_banner, render_case_card, ai_insight_box, empty_state, section_header,
)
from utils.styles import inject_styles

st.set_page_config(page_title="Search | ThreadTrace", page_icon="🔎", layout="wide")
inject_styles()

st.markdown("""
<h1 style="margin-bottom:4px;">🔎 Search Cases</h1>
<p style="color:#6b7280;margin-bottom:20px;">
Keyword search + Cognee semantic search across all follow-up memory</p>
""", unsafe_allow_html=True)
cognee_status_banner()

all_cases = storage.list_cases()
if not all_cases:
    empty_state("📁", "No cases yet", "Add cases first, then search here")
    st.stop()

# ── Search bar ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.2);
border-radius:14px;padding:20px 24px;margin-bottom:20px;">
  <div style="font-weight:600;margin-bottom:12px;">🔍 Keyword Search</div>
""", unsafe_allow_html=True)

search_q = st.text_input("Search by name, location, volunteer, program, or ID",
                          label_visibility="collapsed",
                          placeholder="e.g. Anjali, Kadapa, scholarship…")
f1, f2, f3 = st.columns([2, 2, 1])
with f1: status_f = st.selectbox("Status",    ["All", "active", "closed"])
with f2: vol_f    = st.selectbox("Volunteer", ["All"] + storage.list_volunteers())
with f3: show_ai  = st.checkbox("AI summary", help="Show Cognee summary per result (slower)")
st.markdown("</div>", unsafe_allow_html=True)

results = storage.search_cases(search_q) if search_q else all_cases
if status_f != "All":
    results = [c for c in results if c["status"] == status_f]
if vol_f != "All":
    results = [c for c in results if c.get("assigned_volunteer") == vol_f]

st.markdown(
    f"<div style='color:#6b7280;font-size:0.85rem;margin-bottom:12px;'>"
    f"<strong>{len(results)}</strong> case(s) found"
    + (f" matching <em>'{search_q}'</em>" if search_q else "") + "</div>",
    unsafe_allow_html=True)

if results:
    for case in results:
        render_case_card(case, show_ai_summary=show_ai)
else:
    empty_state("🔍", "No matches", "Try different keywords or remove filters")

st.divider()

# ── Semantic Search ───────────────────────────────────────────────────────────
section_header("🧠 AI Semantic Search",
    "Searches inside follow-up notes, blockers, and promises — not just structured fields")

if not cognee_svc.cognee_available():
    st.warning("Configure Cognee Cloud to enable semantic search.", icon="🔑")
else:
    semantic_q = st.text_input(
        "Describe what you're looking for",
        placeholder=(
            "e.g. 'cases where family hasn't visited the village office' "
            "or 'students who missed a follow-up call'"),
        key="semantic_in")

    if st.button("🔍 Search with AI", type="primary") and semantic_q:
        st.info(
            "⏳ Searching Cognee memory across all cases — "
            "this can take 30–90 seconds. Please wait.",
            icon="🧠",
        )
        with st.spinner("AI semantic search in progress — do not navigate away..."):
            try:
                result = cognee_svc.semantic_search(semantic_q,
                                                    [c["case_id"] for c in all_cases])
                ai_insight_box(f'Semantic Search: "{semantic_q}"', result)
            except TimeoutError:
                st.error(
                    "⏱️ Search timed out. Cognee Cloud is taking too long. "
                    "Try a shorter or more specific query.",
                    icon="⚠️",
                )

    st.divider()

    # Similar cases
    section_header("🔗 Find Similar Cases",
        "Select a case to find others with similar blockers, goals, or situations")
    case_opts  = {f"{c['student_name']} ({c['case_id']})": c for c in all_cases}
    anchor_lbl = st.selectbox("Reference case", list(case_opts.keys()), key="sim_anchor")
    anchor     = case_opts[anchor_lbl]

    if st.button("Find Similar →", type="primary"):
        q = (
            f"Which other cases are similar to {anchor['student_name']}'s? "
            f"Consider: same goal ({anchor['goal']}), similar blockers, "
            f"similar missing documents, or similar situation. "
            f"List student names and what they share."
        )
        other_ids = [c["case_id"] for c in all_cases
                     if c["case_id"] != anchor["case_id"]]
        with st.spinner("Searching for similar cases..."):
            similar = cognee_svc.recall_across_cases(q, other_ids)
        ai_insight_box(f"Cases Similar to {anchor['student_name']}", similar)
