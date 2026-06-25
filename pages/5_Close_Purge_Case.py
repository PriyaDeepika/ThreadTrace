import streamlit as st
from services import storage_service as storage
from services import cognee_service as cognee_svc

st.title("🗂️ Close / Purge Case")

cases = storage.list_cases()
if not cases:
    st.warning("No cases yet.")
    st.stop()

case_options = {f"{c['student_name']} ({c['case_id']}) — {c['status']}": c for c in cases}
selected_label = st.selectbox("Select case", list(case_options.keys()))
selected_case = case_options[selected_label]

st.markdown(f"**Student:** {selected_case['student_name']}")
st.markdown(f"**Status:** {selected_case['status']}")
st.markdown(f"**Goal:** {selected_case['goal']}")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Close case")
    st.caption(
        "Soft action — marks the case as closed (e.g. student got the scholarship). "
        "Data stays in storage and in ThreadTrace's memory, in case it's needed later."
    )
    if selected_case["status"] == "active":
        if st.button("Close this case"):
            storage.update_case_status(selected_case["case_id"], "closed")
            st.success(f"{selected_case['student_name']}'s case marked as closed.")
            st.rerun()
    else:
        st.caption("Already closed.")

with col2:
    st.subheader("Purge case (hard delete)")
    st.caption(
        "⚠️ Permanent — erases this case from local storage AND from ThreadTrace's "
        "memory (Cognee). Use when a student/family requests their data be removed."
    )
    confirm = st.checkbox(f"I understand this permanently deletes {selected_case['student_name']}'s data")
    if st.button("Purge permanently", type="primary", disabled=not confirm):
        with st.spinner("Purging from memory..."):
            cognee_svc.run_async(cognee_svc.forget_case(selected_case["case_id"]))
            storage.purge_case(selected_case["case_id"])
        st.success(f"{selected_case['student_name']}'s case has been permanently purged.")
        st.rerun()
