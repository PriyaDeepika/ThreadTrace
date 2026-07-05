import streamlit as st
from services import storage_service as storage
from services import cognee_service as cognee_svc
from services import query_service as query
from utils.helpers import (
    cognee_status_banner, fmt_date, fmt_datetime,
    render_followup_card, ai_insight_box, empty_state,
)
from utils.styles import inject_styles

st.set_page_config(page_title="Close / Purge | ThreadTrace", page_icon="🗂️", layout="wide")
inject_styles()

st.markdown("""
<h1 style="margin-bottom:4px;">🗂️ Close / Purge Case</h1>
<p style="color:#6b7280;margin-bottom:20px;">
Close (soft) or permanently erase a case from all systems including Cognee memory</p>
""", unsafe_allow_html=True)
cognee_status_banner()

cases = storage.list_cases()
if not cases:
    empty_state("📁", "No cases yet", "Add cases first")
    st.stop()

case_opts = {
    f"{c['student_name']} ({c['case_id']}) [{c['status']}]": c for c in cases}
sel  = st.selectbox("Select case", list(case_opts.keys()))
case = case_opts[sel]
cid  = case["case_id"]

st.divider()

followups = storage.list_followups(cid)
docs      = storage.list_documents(cid)
missing   = query.missing_docs_count(cid)
label     = query.urgency_label(case)

# Case summary banner
st.markdown(f"""
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
border-radius:14px;padding:20px 24px;margin-bottom:24px;">
  <div style="font-size:1.15rem;font-weight:700;margin-bottom:8px;">
    {case['student_name']}
    <code style="font-size:0.7rem;color:#6b7280;margin-left:8px;">{cid}</code>
  </div>
  <div style="color:#9ca3af;font-size:0.85rem;line-height:1.8;">
    📍 {case['location']} &nbsp;·&nbsp; 🎯 {case['goal']} &nbsp;·&nbsp;
    📅 {fmt_date(case['deadline'])} &nbsp;·&nbsp; 👤 {case['assigned_volunteer']}<br>
    📋 {len(followups)} follow-up(s) &nbsp;·&nbsp;
    📄 {len(docs)} document(s) &nbsp;·&nbsp;
    {'<span style="color:#ef4444;">🔴 ' + str(missing) + ' missing</span>' if missing else '🟢 All docs submitted'} &nbsp;·&nbsp;
    Status: <strong>{label}</strong>
  </div>
</div>""", unsafe_allow_html=True)

col_close, col_purge = st.columns(2, gap="large")

# ══════════ CLOSE ══════════
with col_close:
    st.markdown("""
    <div style="background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.2);
    border-radius:14px;padding:20px 22px;margin-bottom:16px;">
      <div style="font-size:1.05rem;font-weight:700;color:#10b981;margin-bottom:8px;">
        ✅ Close Case
      </div>
      <div style="color:#6b7280;font-size:0.88rem;line-height:1.6;">
        <strong>Soft action</strong> — marks case as resolved.<br>
        Data and Cognee memory are <strong>retained</strong>.<br><br>
        Use when: student got the scholarship, application submitted,
        or the case is no longer active.
      </div>
    </div>""", unsafe_allow_html=True)

    if case["status"] == "active":
        outcome = st.text_area("Closing notes (optional)",
            placeholder="e.g. Student received the AP Merit Scholarship. All documents submitted.",
            height=80, key="close_notes")
        if st.button("✅ Close This Case", type="primary", use_container_width=True):
            storage.update_case_status(cid, "closed")
            if outcome:
                storage.add_followup(cid, "System",
                    f"[CASE CLOSED] {outcome}", followup_type="message")
                if cognee_svc.cognee_available():
                    cognee_svc.remember_followup(
                        cid, case["student_name"], "System",
                        f"[CASE CLOSED] Outcome: {outcome}", followup_type="message")
            st.success(f"✅ {case['student_name']}'s case is now closed.")
            st.rerun()
    else:
        st.info("This case is already closed.")
        if st.button("🔄 Re-open Case", use_container_width=True):
            storage.update_case_status(cid, "active")
            st.success("Case re-opened.")
            st.rerun()

# ══════════ PURGE ══════════
with col_purge:
    st.markdown(f"""
    <div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.2);
    border-radius:14px;padding:20px 22px;margin-bottom:16px;">
      <div style="font-size:1.05rem;font-weight:700;color:#ef4444;margin-bottom:8px;">
        🗑️ Purge Case (Hard Delete)
      </div>
      <div style="color:#6b7280;font-size:0.88rem;line-height:1.6;">
        <strong>Permanent</strong> — erases from:<br>
        &nbsp;• Local storage (cases, docs, follow-ups)<br>
        &nbsp;• Cognee Cloud memory (<code>forget()</code>)<br><br>
        Will delete: <strong>{len(followups)}</strong> follow-up(s) and
        <strong>{len(docs)}</strong> document(s).<br>
        <span style="color:#ef4444;font-weight:600;">⚠️ Cannot be undone.</span>
      </div>
    </div>""", unsafe_allow_html=True)

    confirm_text = st.text_input(
        f"Type student name to confirm: **{case['student_name']}**",
        placeholder=case["student_name"], key="purge_confirm")
    confirmed = confirm_text.strip().lower() == case["student_name"].strip().lower()

    if st.button("🗑️ Permanently Purge", type="primary",
                 disabled=not confirmed, use_container_width=True):
        name = case["student_name"]
        if cognee_svc.cognee_available():
            with st.spinner("Erasing from Cognee memory..."):
                cognee_svc.forget_case(cid)
        storage.purge_case(cid)
        st.markdown(f"""
        <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);
        border-radius:12px;padding:18px;text-align:center;">
          <div style="font-size:1.5rem;margin-bottom:8px;">🗑️</div>
          <div style="font-weight:700;">{name} — permanently purged</div>
          <div style="color:#6b7280;font-size:0.85rem;margin-top:6px;">
          Removed from local storage and Cognee memory.</div>
        </div>""", unsafe_allow_html=True)
        st.rerun()

st.divider()

# History preview before acting
with st.expander("📋 View Full Case History Before Acting", expanded=False):
    if followups:
        st.markdown("**Follow-Up History:**")
        for f in followups:
            render_followup_card(f, show_delete=False)
    if docs:
        st.markdown("**Documents:**")
        icons = {"submitted": "🟢", "missing": "🔴", "pending_verification": "🟡"}
        for d in docs:
            st.caption(f"{icons.get(d['status'], '⚪')} {d['doc_name']} — {d['status']}")

# AI pre-closure review
if cognee_svc.cognee_available():
    st.divider()
    st.markdown("#### 🧠 AI Pre-Action Review")
    st.caption("Get an AI summary of this case before closing or purging — so nothing is lost.")
    if st.button("Generate AI Summary Before Acting", use_container_width=True):
        with st.spinner("Recalling from Cognee memory..."):
            summary = cognee_svc.summarize_case(cid, case["student_name"])
        ai_insight_box(f"Final Summary — {case['student_name']}", summary)
