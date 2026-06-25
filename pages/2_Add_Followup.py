import streamlit as st
from datetime import date
from services import storage_service as storage
from services import cognee_service as cognee_svc

st.title("📝 Add Follow-Up")

cases = storage.list_cases(status="active")
if not cases:
    st.warning("No active cases yet. Go to **Add Case** first.")
    st.stop()

case_options = {f"{c['student_name']} ({c['case_id']})": c for c in cases}
selected_label = st.selectbox("Select case", list(case_options.keys()))
selected_case = case_options[selected_label]

with st.form("add_followup_form", clear_on_submit=True):
    worker_name = st.text_input("Your name (worker/volunteer) *")
    note_text = st.text_area(
        "Follow-up note *",
        placeholder='e.g. "Called Anjali today. She still needs income certificate. '
                    'Mentor asked her to submit SOP by July 3."',
        height=120,
    )
    blockers = st.text_input("New blocker (optional)")
    next_step = st.text_input("Next step / promise made (optional)")
    next_followup_date = st.date_input(
        "Next follow-up date (optional)", value=None, min_value=date.today()
    )

    submitted = st.form_submit_button("Save follow-up")

    if submitted:
        if not worker_name or not note_text:
            st.error("Worker name and follow-up note are required.")
        else:
            # 1. Local structured copy — powers dashboard filtering/sorting
            storage.add_followup(
                case_id=selected_case["case_id"],
                worker_name=worker_name,
                note_text=note_text,
                blockers=blockers,
                next_step=next_step,
                next_followup_date=next_followup_date.isoformat() if next_followup_date else None,
            )

            # 2. Send the messy text to Cognee — THIS is the memory layer call
            with st.spinner("Saving to ThreadTrace memory..."):
                cognee_svc.run_async(
                    cognee_svc.remember_followup(
                        case_id=selected_case["case_id"],
                        student_name=selected_case["student_name"],
                        worker_name=worker_name,
                        note_text=note_text,
                        blockers=blockers,
                        next_step=next_step,
                    )
                )

            st.success("Follow-up saved and remembered.")

st.divider()
st.subheader(f"Follow-up history — {selected_case['student_name']}")
followups = storage.list_followups(selected_case["case_id"])
if followups:
    for f in followups:
        with st.expander(f"{f['date'][:10]} — {f['worker_name']}"):
            st.write(f["note_text"])
            if f["blockers"]:
                st.warning(f"Blocker: {f['blockers']}")
            if f["next_step"]:
                st.info(f"Next step: {f['next_step']}")
else:
    st.caption("No follow-ups logged yet for this case.")
