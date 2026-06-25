"""
app.py — ThreadTrace main entry point.

Run with: streamlit run app.py
Pages live in pages/ and are auto-discovered by Streamlit's multipage nav.
"""

import streamlit as st
from services import query_service as query

st.set_page_config(page_title="ThreadTrace", page_icon="🌉", layout="wide")

st.title("🌉 ThreadTrace")
st.caption("An AI memory assistant for education-support NGOs and mentors.")

st.markdown(
    "ThreadTrace remembers each student's case history, missing documents, "
    "deadlines, and follow-up actions across multiple volunteers and sessions — "
    "so no student falls through the cracks due to lost context."
)

st.divider()

summary = query.dashboard_summary()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Active cases", summary["active_count"])
col2.metric("Urgent", len(summary["urgent_cases"]))
col3.metric("Overdue follow-up", len(summary["overdue_cases"]))
col4.metric("Missing documents", summary["missing_docs_total"])

st.divider()
st.markdown(
    "**Use the sidebar to navigate:**\n"
    "- **Add Case** — register a new student case\n"
    "- **Add Follow-Up** — log a call/visit, this feeds ThreadTrace's memory\n"
    "- **Ask ThreadTrace** — ask questions across one case or your whole caseload\n"
    "- **Dashboard** — see urgent cases, overdue follow-ups, missing docs\n"
    "- **Close / Purge Case** — archive a case, or fully erase its memory"
)
