import streamlit as st
from datetime import date, timedelta
from services import storage_service as storage
from services import cognee_service as cognee_svc
from utils.helpers import (
    cognee_status_banner, fmt_date, fmt_datetime,
    ai_insight_box, render_followup_card, empty_state,
)
from utils.styles import inject_styles

st.set_page_config(page_title="Add Follow-Up | ThreadTrace", page_icon="📝", layout="wide")
inject_styles()

st.markdown("""
<h1 style="margin-bottom:4px;">📝 Log Follow-Up</h1>
<p style="color:#6b7280;margin-bottom:20px;">
Every interaction is committed to Cognee memory instantly</p>
""", unsafe_allow_html=True)
cognee_status_banner()

cases = storage.list_cases(status="active")
if not cases:
    empty_state("📁", "No active cases yet",
                "Go to Add Case to register your first student", "➕ Add Case")
    st.stop()

case_options = {
    f"{c['student_name']} ({c['case_id']}) — {c['assigned_volunteer']}": c
    for c in cases
}
selected_label = st.selectbox("Select case", list(case_options.keys()))
selected_case  = case_options[selected_label]

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.divider()

left, right = st.columns([3, 2], gap="large")

with left:
    # AI pre-briefing
    if cognee_svc.cognee_available():
        if st.button("🧠 What should I cover in this follow-up?",
                     use_container_width=True, type="primary"):
            with st.spinner("Checking case memory for suggestions..."):
                suggestion = cognee_svc.suggest_next_action(
                    selected_case["case_id"], selected_case["student_name"])
            ai_insight_box(
                f"Suggested Focus — {selected_case['student_name']}", suggestion)
            st.session_state[f"pre_{selected_case['case_id']}"] = suggestion
        elif f"pre_{selected_case['case_id']}" in st.session_state:
            ai_insight_box(
                f"Suggested Focus — {selected_case['student_name']}",
                st.session_state[f"pre_{selected_case['case_id']}"])

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("#### Log the Interaction")

    with st.form("add_followup_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            worker_name = st.text_input("Your name *",
                                        placeholder="Volunteer / worker name")
        with c2:
            followup_type = st.selectbox("Interaction type", storage.FOLLOWUP_TYPES,
                format_func=lambda t: {
                    "call": "📞 Phone call", "visit": "🏠 Home visit",
                    "message": "💬 WhatsApp/SMS", "email": "📧 Email",
                }.get(t, t))

        note_text = st.text_area(
            "What happened / what was discussed? *",
            placeholder=(
                "e.g. Called Anjali today. She confirmed caste certificate is ready. "
                "Income certificate still missing — family visiting village office "
                "tomorrow. Asked her to send a photo once received."
            ),
            height=140,
        )
        c3, c4 = st.columns(2)
        with c3:
            blockers = st.text_input("Blockers / obstacles",
                placeholder="e.g. Father not available this week")
        with c4:
            next_step = st.text_input("Next action promised",
                placeholder="e.g. Follow up in 3 days")

        next_followup_date = st.date_input(
            "Schedule next follow-up (optional)",
            value=None, min_value=date.today() + timedelta(days=1))

        submitted = st.form_submit_button(
            "💾 Save & Commit to Memory", type="primary", use_container_width=True)

    if submitted:
        if not worker_name or not note_text:
            st.error("Worker name and note are required.")
        else:
            storage.add_followup(
                case_id=selected_case["case_id"], worker_name=worker_name,
                note_text=note_text, blockers=blockers, next_step=next_step,
                next_followup_date=next_followup_date.isoformat()
                    if next_followup_date else None,
                followup_type=followup_type,
            )
            if cognee_svc.cognee_available():
                with st.spinner("🧠 Committing to Cognee memory..."):
                    cognee_svc.remember_followup(
                        case_id=selected_case["case_id"],
                        student_name=selected_case["student_name"],
                        worker_name=worker_name, note_text=note_text,
                        blockers=blockers, next_step=next_step,
                        followup_type=followup_type,
                    )
                st.markdown("""
                <div style="background:rgba(16,185,129,0.08);border:1px solid
                rgba(16,185,129,0.3);border-radius:12px;padding:14px 18px;margin:10px 0;">
                  ✅ <strong>Saved</strong> — Follow-up committed to Cognee memory
                </div>""", unsafe_allow_html=True)
            else:
                st.success("✅ Follow-up saved locally.")
                st.warning("Cognee not configured — not added to AI memory.", icon="🔑")

            if next_followup_date:
                st.info(f"📅 Next follow-up scheduled: {fmt_date(next_followup_date.isoformat())}")

with right:
    # Case snapshot card
    c = selected_case
    st.markdown(f"""
    <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.2);
    border-radius:14px;padding:20px 22px;margin-bottom:16px;">
      <div style="font-size:1.05rem;font-weight:700;margin-bottom:8px;">
        🗂️ {c['student_name']}
      </div>
      <div style="color:#9ca3af;font-size:0.85rem;line-height:1.8;">
        📍 {c['location']}<br>
        🎯 {c['goal']}<br>
        📋 {c['target_program_or_scholarship']}<br>
        📅 Deadline: {fmt_date(c['deadline'])}<br>
        👤 {c['assigned_volunteer']}
      </div>
    </div>""", unsafe_allow_html=True)

    # Document status
    docs = storage.list_documents(selected_case["case_id"])
    if docs:
        st.markdown("**📄 Document Status**")
        icons = {"submitted": "🟢", "missing": "🔴", "pending_verification": "🟡"}
        for doc in docs:
            st.caption(f"{icons.get(doc['status'], '⚪')} {doc['doc_name']}")

    # Last 3 follow-ups
    st.markdown("**📋 Last 3 Follow-Ups**")
    followups = storage.list_followups(selected_case["case_id"])[:3]
    if followups:
        for f in followups:
            with st.expander(
                f"{f['date'][:10]} — {f['worker_name']}", expanded=False):
                st.write(f["note_text"][:200])
                if f.get("blockers"):
                    st.caption(f"🚧 {f['blockers']}")
    else:
        st.caption("No follow-ups yet.")
