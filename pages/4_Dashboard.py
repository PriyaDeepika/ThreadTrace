import streamlit as st
from services import storage_service as storage
from services import query_service as query

st.title("📊 Case Overview Dashboard")

summary = query.dashboard_summary()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Active cases", summary["active_count"])
col2.metric("Urgent", len(summary["urgent_cases"]))
col3.metric("Overdue follow-up", len(summary["overdue_cases"]))
col4.metric("Missing documents", summary["missing_docs_total"])

st.divider()

tab1, tab2, tab3 = st.tabs(["🔥 Urgent cases", "⏰ Overdue follow-ups", "📅 Deadlines this week"])

with tab1:
    if summary["urgent_cases"]:
        for c in summary["urgent_cases"]:
            st.error(
                f"**{c['student_name']}** ({c['case_id']}) — deadline {c['deadline']} — "
                f"volunteer: {c['assigned_volunteer']}"
            )
    else:
        st.success("No urgent cases right now.")

with tab2:
    if summary["overdue_cases"]:
        for c in summary["overdue_cases"]:
            last = storage.last_followup_date(c["case_id"])
            last_str = last.isoformat() if last else "never"
            st.warning(f"**{c['student_name']}** ({c['case_id']}) — last follow-up: {last_str}")
    else:
        st.success("Everyone's been followed up recently.")

with tab3:
    this_week = query.cases_with_deadline_this_week()
    if this_week:
        for c in this_week:
            st.info(f"**{c['student_name']}** ({c['case_id']}) — deadline {c['deadline']}")
    else:
        st.caption("No deadlines in the next 7 days.")
