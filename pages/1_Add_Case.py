import streamlit as st
from datetime import date
from services import storage_service as storage

st.title("➕ Add Student Case")

with st.form("add_case_form", clear_on_submit=True):
    student_name = st.text_input("Student name *")
    location = st.text_input("Location / village / district *")
    goal = st.selectbox(
        "Goal",
        ["Scholarship", "Admission support", "Fee reimbursement",
         "Hostel support", "Fee concession", "Other"],
    )
    target_program = st.text_input("Target program / scholarship name *")
    deadline = st.date_input("Deadline", min_value=date.today())
    assigned_volunteer = st.text_input("Assigned volunteer *")
    summary = st.text_area("Initial notes / summary (optional)")

    submitted = st.form_submit_button("Create case")

    if submitted:
        if not student_name or not location or not target_program or not assigned_volunteer:
            st.error("Please fill in all required fields (marked *).")
        else:
            case = storage.create_case(
                student_name=student_name,
                location=location,
                goal=goal,
                target_program_or_scholarship=target_program,
                deadline=deadline.isoformat(),
                assigned_volunteer=assigned_volunteer,
                summary=summary,
            )
            st.success(f"Case created for {student_name} — case_id: `{case['case_id']}`")
            st.info("Next: go to **Add Follow-Up** to log the first interaction with this student.")

st.divider()
st.subheader("Existing cases")
cases = storage.list_cases()
if cases:
    st.dataframe(
        [{"case_id": c["case_id"], "student": c["student_name"], "goal": c["goal"],
          "deadline": c["deadline"], "status": c["status"], "volunteer": c["assigned_volunteer"]}
         for c in cases],
        use_container_width=True,
    )
else:
    st.caption("No cases yet. Create your first one above, or load demo data — see seed/demo_seed.py.")
