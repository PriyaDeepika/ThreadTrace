import streamlit as st
from services import storage_service as storage
from services import cognee_service as cognee_svc

st.title("💬 Ask ThreadTrace")
st.caption("Ask about one case, or across your whole caseload.")

mode = st.radio("Scope", ["Single case", "Across all active cases"], horizontal=True)

if mode == "Single case":
    cases = storage.list_cases()
    if not cases:
        st.warning("No cases yet. Go to **Add Case** first.")
        st.stop()

    case_options = {f"{c['student_name']} ({c['case_id']})": c for c in cases}
    selected_label = st.selectbox("Select case", list(case_options.keys()))
    selected_case = case_options[selected_label]

    st.markdown("**Try asking:**")
    st.code(f"What's pending for {selected_case['student_name']}?\n"
             f"Summarize {selected_case['student_name']}'s case.")

    question = st.text_input("Your question")
    if st.button("Ask", type="primary") and question:
        with st.spinner("Recalling..."):
            answer = cognee_svc.run_async(
                cognee_svc.recall_case(selected_case["case_id"], question)
            )
        st.markdown("### Answer")
        st.write(answer)

else:
    active_cases = storage.list_cases(status="active")
    if not active_cases:
        st.warning("No active cases yet.")
        st.stop()

    st.markdown("**Try asking:**")
    st.code("Which students have deadlines this week?\n"
            "Who hasn't been followed up in 10 days?\n"
            "What documents are missing across all cases?")

    question = st.text_input("Your question")
    if st.button("Ask", type="primary") and question:
        case_ids = [c["case_id"] for c in active_cases]
        with st.spinner("Recalling across all cases..."):
            answer = cognee_svc.run_async(
                cognee_svc.recall_across_cases(question, case_ids)
            )
        st.markdown("### Answer")
        st.write(answer)
