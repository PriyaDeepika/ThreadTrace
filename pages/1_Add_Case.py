import streamlit as st
from datetime import date, timedelta
from services import storage_service as storage
from services import cognee_service as cognee_svc
from services import query_service as query
from utils.helpers import cognee_status_banner, fmt_date, empty_state, section_header
from utils.styles import inject_styles

st.set_page_config(page_title="Add Case | ThreadTrace", page_icon="➕", layout="wide")
inject_styles()

st.markdown("""
<h1 style="margin-bottom:4px;">➕ Add Student Case</h1>
<p style="color:#6b7280;margin-bottom:20px;">
Register a new student and immediately seed Cognee AI memory</p>
""", unsafe_allow_html=True)
cognee_status_banner()

tab_new, tab_list = st.tabs(["📝 New Case", "📋 All Cases"])

# ── TAB: New Case ─────────────────────────────────────────────────────────────
with tab_new:
    with st.form("add_case_form", clear_on_submit=True):
        st.markdown("#### 👤 Student Details")
        c1, c2, c3 = st.columns(3)
        with c1: student_name   = st.text_input("Full name *")
        with c2: age            = st.text_input("Age")
        with c3: contact_number = st.text_input("Contact number")

        c4, c5 = st.columns(2)
        with c4:
            location = st.text_input("Location / village / district *")
        with c5:
            education_level = st.selectbox("Education level",
                ["", "Class 10", "Class 12", "Diploma",
                 "Undergraduate", "Postgraduate", "Other"])

        st.markdown("#### 🎯 Case Details")
        c6, c7 = st.columns(2)
        with c6: goal           = st.selectbox("Goal *", storage.GOALS)
        with c7: target_program = st.text_input("Target program / scholarship *")

        c8, c9 = st.columns(2)
        with c8:
            deadline = st.date_input("Application deadline *",
                min_value=date.today(), value=date.today() + timedelta(days=14))
        with c9:
            assigned_volunteer = st.text_input("Assigned volunteer *")

        summary = st.text_area("Initial notes",
            placeholder="e.g. First-generation learner. Family income below ₹2L/year.",
            height=90)

        st.markdown("#### 📄 Initial Documents")
        dc1, dc2 = st.columns(2)
        with dc1:
            selected_docs = st.multiselect("Documents required", storage.COMMON_DOCS)
        with dc2:
            default_doc_status = st.selectbox("Initial status for all",
                ["missing", "pending_verification", "submitted"])

        submitted = st.form_submit_button(
            "🚀 Create Case + Seed Memory", type="primary", use_container_width=True)

    if submitted:
        if not student_name or not location or not target_program or not assigned_volunteer:
            st.error("Please fill all required fields (marked *).")
        else:
            case = storage.create_case(
                student_name=student_name, location=location, goal=goal,
                target_program_or_scholarship=target_program,
                deadline=deadline.isoformat(), assigned_volunteer=assigned_volunteer,
                summary=summary, contact_number=contact_number,
                age=age, education_level=education_level,
            )
            for doc_name in selected_docs:
                storage.add_document(case["case_id"], doc_name, default_doc_status)

            if cognee_svc.cognee_available():
                with st.spinner("🧠 Seeding Cognee memory..."):
                    cognee_svc.remember_case_context(
                        case_id=case["case_id"], student_name=student_name,
                        location=location, goal=goal, program=target_program,
                        deadline=deadline.isoformat(), volunteer=assigned_volunteer,
                        summary=summary,
                    )
                    if selected_docs:
                        doc_list = ", ".join(
                            f"{d} ({default_doc_status})" for d in selected_docs)
                        cognee_svc.remember_document_update(
                            case["case_id"], student_name,
                            f"Initial documents: {doc_list}", default_doc_status)

            cognee_badge = (
                '<div style="color:#10b981;font-size:0.83rem;margin-top:8px;">🧠 Cognee memory seeded</div>'
                if cognee_svc.cognee_available() else
                '<div style="color:#f59e0b;font-size:0.83rem;margin-top:8px;">⚠️ Cognee not configured — local only</div>'
            )
            st.markdown(f"""
            <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);
            border-radius:14px;padding:22px 26px;margin:14px 0;">
              <div style="font-size:1.5rem;margin-bottom:8px;">✅</div>
              <div style="font-weight:700;font-size:1.1rem;">{student_name}</div>
              <div style="color:#9ca3af;font-size:0.88rem;margin-top:4px;">
                📅 Deadline: {fmt_date(deadline.isoformat())} &nbsp;·&nbsp;
                👤 {assigned_volunteer} &nbsp;·&nbsp;
                🆔 <code style="background:rgba(255,255,255,0.08);
                padding:1px 6px;border-radius:4px;">{case['case_id']}</code>
              </div>
              {cognee_badge}
            </div>""", unsafe_allow_html=True)
            st.info("Next → **Add Follow-Up** to log your first contact.", icon="💡")

# ── TAB: All Cases ────────────────────────────────────────────────────────────
with tab_list:
    section_header("All Cases", "Filter and sort your caseload")

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        status_f = st.selectbox("Status", ["All", "active", "closed"])
    with fc2:
        volunteers = ["All"] + storage.list_volunteers()
        vol_f = st.selectbox("Volunteer", volunteers)
    with fc3:
        goal_f = st.selectbox("Goal", ["All"] + storage.GOALS)
    with fc4:
        sort_by = st.selectbox("Sort by",
            ["Newest first", "Deadline soon", "Name A–Z"])

    cases = storage.list_cases(
        status=None if status_f == "All" else status_f,
        volunteer=None if vol_f == "All" else vol_f,
        goal=None if goal_f == "All" else goal_f,
    )
    if sort_by == "Deadline soon":
        cases = sorted(cases, key=lambda c: c.get("deadline", "9999"))
    elif sort_by == "Name A–Z":
        cases = sorted(cases, key=lambda c: c.get("student_name", ""))

    st.caption(f"{len(cases)} case(s) found")
    if cases:
        rows = [{
            "ID": c["case_id"], "Student": c["student_name"],
            "Location": c["location"], "Goal": c["goal"],
            "Deadline": c["deadline"], "Volunteer": c["assigned_volunteer"],
            "Status": query.urgency_label(c),
        } for c in cases]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        empty_state("🔍", "No cases match filters", "Try adjusting the filters above")
