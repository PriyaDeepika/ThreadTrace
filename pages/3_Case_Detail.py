import streamlit as st
from datetime import date, timedelta
from services import storage_service as storage
from services import cognee_service as cognee_svc
from services import query_service as query
from utils.helpers import (
    cognee_status_banner, render_followup_card, render_document_table,
    fmt_date, fmt_datetime, ai_insight_box, urgency_css, empty_state,
)
from utils.styles import inject_styles

st.set_page_config(page_title="Case Detail | ThreadTrace", page_icon="🗂️", layout="wide")
inject_styles()

st.markdown("""
<h1 style="margin-bottom:4px;">🗂️ Case Detail</h1>
<p style="color:#6b7280;margin-bottom:20px;">
Full case view with AI memory panel</p>
""", unsafe_allow_html=True)
cognee_status_banner()

cases = storage.list_cases()
if not cases:
    empty_state("📁", "No cases yet", "Go to Add Case to register your first student")
    st.stop()

case_options = {
    f"{c['student_name']} ({c['case_id']}) [{c['status']}]": c for c in cases}
selected_label = st.selectbox("Select case", list(case_options.keys()))
case    = case_options[selected_label]
case_id = case["case_id"]

st.divider()
main_col, ai_col = st.columns([3, 2], gap="large")

# ═══════════ LEFT — case info, docs, follow-ups ═══════════
with main_col:
    label      = query.urgency_label(case)
    tc, bg, br = urgency_css(label)
    missing    = query.missing_docs_count(case_id)

    # Status bar
    _missing_html = (
        f'&nbsp;·&nbsp; <span style="color:#ef4444;">📄 {missing} doc(s) missing</span>'
        if missing else ''
    )
    _status_html = (
        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
        f'border-radius:14px;padding:18px 22px;margin-bottom:20px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        f'<div>'
        f'<div style="font-size:1.3rem;font-weight:700;margin-bottom:6px;">'
        f'{case["student_name"]}'
        f'<span style="font-size:0.72rem;font-weight:400;color:#6b7280;'
        f'margin-left:8px;font-family:monospace;">{case_id}</span></div>'
        f'<div style="color:#9ca3af;font-size:0.85rem;line-height:1.8;">'
        f'📍 {case["location"]} &nbsp;·&nbsp; 🎯 {case["goal"]} &nbsp;·&nbsp; 👤 {case["assigned_volunteer"]}<br>'
        f'📋 {case["target_program_or_scholarship"]} &nbsp;·&nbsp; 📅 Deadline: {fmt_date(case["deadline"])}'
        f'{_missing_html}</div></div>'
        f'<span style="background:{bg};color:{tc};border:1px solid {br};'
        f'border-radius:20px;padding:5px 14px;font-size:0.82rem;font-weight:700;'
        f'white-space:nowrap;">{label}</span>'
        f'</div></div>'
    )
    st.markdown(_status_html, unsafe_allow_html=True)

    # Edit Case
    with st.expander("✏️ Edit Case Details", expanded=False):
        with st.form(f"edit_{case_id}"):
            ec1, ec2 = st.columns(2)
            with ec1:
                new_name    = st.text_input("Student name",  value=case["student_name"])
                new_loc     = st.text_input("Location",      value=case["location"])
                new_contact = st.text_input("Contact",       value=case.get("contact_number", ""))
                new_age     = st.text_input("Age",           value=case.get("age", ""))
            with ec2:
                new_goal = st.selectbox("Goal", storage.GOALS,
                    index=storage.GOALS.index(case["goal"])
                    if case["goal"] in storage.GOALS else 0)
                new_prog = st.text_input("Program / Scholarship",
                    value=case["target_program_or_scholarship"])
                new_dl   = st.date_input("Deadline",
                    value=date.fromisoformat(case["deadline"]))
                new_vol  = st.text_input("Assigned volunteer",
                    value=case["assigned_volunteer"])
            new_summary = st.text_area("Notes", value=case.get("summary", ""), height=70)
            if st.form_submit_button("💾 Save Changes", type="primary"):
                storage.update_case(case_id,
                    student_name=new_name, location=new_loc, goal=new_goal,
                    target_program_or_scholarship=new_prog,
                    deadline=new_dl.isoformat(), assigned_volunteer=new_vol,
                    summary=new_summary, contact_number=new_contact, age=new_age)
                # Sync updated fields to Cognee so recall queries stay current
                if cognee_svc.cognee_available():
                    cognee_svc.remember_case_context(
                        case_id=case_id, student_name=new_name,
                        location=new_loc, goal=new_goal, program=new_prog,
                        deadline=new_dl.isoformat(), volunteer=new_vol,
                        summary=f"[CASE UPDATED] {new_summary}",
                    )
                st.success("Case updated.")
                st.rerun()

    # Documents
    st.markdown("### 📄 Documents")
    docs = storage.list_documents(case_id)
    with st.expander("➕ Add Document", expanded=len(docs) == 0):
        with st.form(f"add_doc_{case_id}", clear_on_submit=True):
            ad1, ad2, ad3 = st.columns(3)
            with ad1: doc_name   = st.selectbox("Document", storage.COMMON_DOCS)
            with ad2: doc_status = st.selectbox("Status",   storage.VALID_DOC_STATUSES)
            with ad3: doc_notes  = st.text_input("Notes")
            if st.form_submit_button("Add", type="primary"):
                storage.add_document(case_id, doc_name, doc_status, doc_notes)
                if cognee_svc.cognee_available():
                    cognee_svc.remember_document_update(
                        case_id, case["student_name"], doc_name, doc_status, doc_notes)
                st.success(f"Added: {doc_name}")
                st.rerun()

    updates = render_document_table(docs, editable=True)
    for doc_id, new_status in updates:
        doc = next((d for d in docs if d["doc_id"] == doc_id), None)
        storage.update_document(doc_id, status=new_status)
        if cognee_svc.cognee_available() and doc:
            cognee_svc.remember_document_update(
                case_id, case["student_name"], doc["doc_name"], new_status)
        st.rerun()

    # Follow-up history
    st.markdown("### 📋 Follow-Up History")
    followups = storage.list_followups(case_id)

    with st.expander("➕ Quick Follow-Up", expanded=False):
        with st.form(f"quick_fup_{case_id}", clear_on_submit=True):
            qf1, qf2 = st.columns(2)
            with qf1: q_worker = st.text_input("Your name *")
            with qf2: q_type   = st.selectbox("Type", storage.FOLLOWUP_TYPES)
            q_note    = st.text_area("Note *", height=80)
            q_blocker = st.text_input("Blocker (optional)")
            q_next    = st.text_input("Next step (optional)")
            if st.form_submit_button("Save & Remember", type="primary"):
                if q_worker and q_note:
                    storage.add_followup(case_id, q_worker, q_note,
                        q_blocker, q_next, followup_type=q_type)
                    if cognee_svc.cognee_available():
                        cognee_svc.remember_followup(
                            case_id, case["student_name"],
                            q_worker, q_note, q_blocker, q_next, q_type)
                    st.success("Saved.")
                    st.rerun()

    if followups:
        for f in followups:
            deleted = render_followup_card(f, show_delete=True)
            if deleted:
                storage.delete_followup(f["followup_id"])
                st.rerun()
    else:
        empty_state("📋", "No follow-ups yet",
                    "Use the Quick Follow-Up above or the Add Follow-Up page")

# ═══════════ RIGHT — AI Memory Panel ═══════════
with ai_col:
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(139,92,246,0.07));'
        'border:1px solid rgba(99,102,241,0.25);border-radius:14px;padding:16px 20px;margin-bottom:16px;">'
        '<div style="font-weight:700;font-size:1.05rem;margin-bottom:4px;">🧠 AI Case Intelligence</div>'
        '<div style="color:#6b7280;font-size:0.82rem;">'
        'Powered by Cognee — asks questions across this case\'s full memory</div></div>',
        unsafe_allow_html=True,
    )

    if not cognee_svc.cognee_available():
        st.warning("Configure Cognee Cloud to see AI insights.", icon="🔑")
    else:
        def ai_btn(label, session_key, question):
            if st.button(label, use_container_width=True, key=f"btn_{session_key}"):
                with st.spinner("Recalling from memory..."):
                    result = cognee_svc.recall_case(case_id, question)
                st.session_state[session_key] = result
            if session_key in st.session_state:
                ai_insight_box(label.split(maxsplit=1)[1], st.session_state[session_key])
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if st.button("📋 Generate Case Summary", type="primary", use_container_width=True):
            with st.spinner("Summarizing from memory..."):
                result = cognee_svc.summarize_case(case_id, case["student_name"])
            st.session_state[f"sum_{case_id}"] = result
        if f"sum_{case_id}" in st.session_state:
            ai_insight_box("Case Summary", st.session_state[f"sum_{case_id}"])
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        ai_btn("🎯 Suggest Next Action",    f"act_{case_id}",
               f"What is the single most important next action for {case['student_name']}'s case?")
        ai_btn("🚧 Extract Pending Blockers", f"blk_{case_id}",
               f"List all unresolved blockers for {case['student_name']}. What is still preventing progress?")
        ai_btn("📅 Summarize Timeline",    f"tl_{case_id}",
               f"Summarize the timeline of {case['student_name']}'s case in chronological order.")
        ai_btn("⚠️ Assess Risk Level",     f"rsk_{case_id}",
               f"Rate the risk (Low/Medium/High) that {case['student_name']} won't meet their goal. Explain warning signs.")

        st.divider()
        st.markdown("**💬 Ask About This Case**")
        free_q = st.text_input("Your question", key=f"fq_{case_id}",
                               placeholder="e.g. What did we promise last time?")
        if st.button("Ask →", key=f"ask_{case_id}") and free_q:
            with st.spinner("Recalling..."):
                answer = cognee_svc.recall_case(case_id, free_q)
            ai_insight_box("Answer", answer)

        st.divider()
        if st.button("⚡ Improve Memory Quality", use_container_width=True,
                     help="Runs Cognee's improve/memify on this case"):
            with st.spinner("Improving memory..."):
                cognee_svc.improve_case_memory(case_id)
            st.success("Memory enrichment complete.")
