import streamlit as st
from services import storage_service as storage
from services import cognee_service as cognee_svc
from utils.helpers import cognee_status_banner, cognee_guard, ai_insight_box, empty_state
from utils.styles import inject_styles

st.set_page_config(page_title="Ask ThreadTrace | ThreadTrace", page_icon="💬", layout="wide")
inject_styles()

st.markdown("""
<h1 style="margin-bottom:4px;">💬 Ask ThreadTrace</h1>
<p style="color:#6b7280;margin-bottom:20px;">
Natural language querying powered by Cognee's graph-vector memory</p>
""", unsafe_allow_html=True)
cognee_status_banner()

if not cognee_guard():
    st.stop()

if "query_history" not in st.session_state:
    st.session_state["query_history"] = []

cases      = storage.list_cases()
active     = storage.list_cases(status="active")
case_ids   = [c["case_id"] for c in cases]
active_ids = [c["case_id"] for c in active]

if not cases:
    empty_state("📁", "No cases yet",
                "Add cases and follow-ups first — then ask questions about them")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🔍 Single Case", "🌐 Across All Cases", "⚡ Preset Queries"])

# ── Single case ───────────────────────────────────────────────────────────────
with tab1:
    case_opts = {f"{c['student_name']} ({c['case_id']})": c for c in cases}
    sel       = st.selectbox("Select case", list(case_opts.keys()), key="ask_single")
    selected  = case_opts[sel]

    st.markdown("**Try these:**")
    examples = [
        f"Summarize {selected['student_name']}'s case",
        "What's still pending?",
        "What blockers were mentioned?",
        "What was promised last time?",
        "What documents are missing?",
    ]
    clicked = None
    cols = st.columns(len(examples))
    for i, q in enumerate(examples):
        if cols[i].button(q, key=f"ex_s_{i}"):
            clicked = q

    question = st.text_input("Or type your question", key="ask_single_q",
                              value=clicked or "",
                              placeholder="e.g. What did we promise last time?")
    if st.button("Ask →", type="primary", key="ask_single_btn") and question:
        with st.spinner(f"Recalling from {selected['student_name']}'s memory..."):
            try:
                answer = cognee_svc.recall_case(selected["case_id"], question)
                ai_insight_box(f"{selected['student_name']} — {question[:60]}", answer)
            except TimeoutError:
                st.error("⏱️ Cognee timed out. Try again.", icon="⚠️")
        st.session_state["query_history"].insert(0,
            {"q": question, "a": answer, "scope": selected["student_name"]})

# ── All cases ─────────────────────────────────────────────────────────────────
with tab2:
    scope = st.radio("Scope",
        ["Active cases only", "All cases (including closed)"],
        horizontal=True, key="ask_scope")
    ids = active_ids if scope == "Active cases only" else case_ids

    cross_examples = [
        "Who hasn't been followed up in 10 days?",
        "Which students have deadlines this week?",
        "What are the most common blockers?",
        "Which cases are at risk of missing their deadline?",
        "What documents are still missing across all cases?",
        "Which volunteer has the most urgent cases?",
        "Give a full caseload summary",
    ]

    st.markdown("**Quick queries:**")
    cross_clicked = None
    for i in range(0, len(cross_examples), 3):
        row_items = cross_examples[i:i+3]
        cols = st.columns(len(row_items))
        for j, q in enumerate(row_items):
            if cols[j].button(q, key=f"ex_c_{i+j}"):
                cross_clicked = q

    cross_q = st.text_input("Or type your question", key="ask_cross_q",
                             value=cross_clicked or "",
                             placeholder="e.g. Which cases need immediate attention?")
    if st.button("Ask →", type="primary", key="ask_cross_btn") and cross_q:
        with st.spinner(f"Querying across {len(ids)} cases — please wait..."):
            try:
                answer = cognee_svc.recall_across_cases(cross_q, ids)
                ai_insight_box(f"{len(ids)} cases — {cross_q[:60]}", answer)
            except TimeoutError:
                st.error("⏱️ Cognee timed out. Try a more specific query.", icon="⚠️")
        st.session_state["query_history"].insert(0,
            {"q": cross_q, "a": answer, "scope": f"{len(ids)} cases"})

# ── Presets ───────────────────────────────────────────────────────────────────
with tab3:
    st.markdown(
        "These presets use Cognee to surface patterns and risks "
        "that are impossible to find manually across a full caseload.")

    presets = {
        "🚧 Extract All Active Blockers": (
            "List all unresolved blockers across all cases. Group by student name. "
            "Which blockers are recurring across multiple cases?"
        ),
        "⚠️ Identify At-Risk Cases": (
            "Which cases show warning signs of not meeting their goal? "
            "Look for: missed follow-ups, recurring blockers, missing documents "
            "close to deadline, or no recent progress. List student names."
        ),
        "📄 Missing Document Analysis": (
            "Which students are missing which documents? Are there patterns "
            "(e.g. everyone missing income certificate)? "
            "Which missing documents are most urgent given deadlines?"
        ),
        "👥 Volunteer Workload Intelligence": (
            "For each volunteer, summarize: how many cases, which are most urgent, "
            "what their cases have in common. "
            "Are any volunteers overloaded with critical cases?"
        ),
        "🔁 Recurring Patterns": (
            "What patterns repeat across cases? Common blockers? Common document issues? "
            "What do they reveal about systemic gaps in the support process?"
        ),
        "✅ Success Signals": (
            "Which cases show the most progress recently? What actions correlate "
            "with cases moving forward? What can we learn from successful cases?"
        ),
    }

    for preset_name, preset_query in presets.items():
        with st.expander(preset_name):
            st.caption(f"_{preset_query[:130]}…_")
            if st.button(f"Run →", key=f"preset_{preset_name}"):
                with st.spinner("Analyzing across all cases — please wait..."):
                    try:
                        answer = cognee_svc.recall_across_cases(preset_query, case_ids)
                        ai_insight_box(preset_name, answer)
                    except TimeoutError:
                        st.error("⏱️ Cognee timed out. Try again.", icon="⚠️")
                st.session_state["query_history"].insert(0,
                    {"q": preset_name, "a": answer, "scope": f"{len(case_ids)} cases"})

# ── History ───────────────────────────────────────────────────────────────────
if st.session_state["query_history"]:
    st.divider()
    st.markdown("#### 🕒 Query History (this session)")
    for i, item in enumerate(st.session_state["query_history"][:8]):
        with st.expander(
            f"[{item['scope']}] {item['q'][:70]}", expanded=(i == 0)):
            ai_insight_box("Recalled Answer", item["a"])
