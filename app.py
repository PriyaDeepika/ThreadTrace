import json
import streamlit as st
from services import storage_service as storage
from services import query_service as query
from services import cognee_service as cognee_svc
from utils.helpers import (
    cognee_status_banner, fmt_datetime, followup_type_icon,
    ai_insight_box, stat_card, empty_state,
)
from utils.styles import inject_styles

st.set_page_config(
    page_title="ThreadTrace — AI Case Memory",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_styles()

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(139,92,246,0.08));
border:1px solid rgba(99,102,241,0.2);border-radius:16px;padding:28px 32px;margin-bottom:24px;">
  <div style="display:flex;align-items:center;gap:16px;">
    <div style="font-size:2.8rem;">🌉</div>
    <div>
      <h1 style="margin:0;font-size:2rem;font-weight:800;
      background:linear-gradient(135deg,#6366f1,#a78bfa);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        ThreadTrace
      </h1>
      <p style="margin:4px 0 0 0;color:#9ca3af;font-size:0.95rem;">
        AI-powered case memory for NGO education support workers
      </p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

cognee_status_banner()

# ── Metrics ───────────────────────────────────────────────────────────────────
summary = query.dashboard_summary()
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
with c1: stat_card("Active Cases",      str(summary["active_count"]),      "📁", "#6366f1")
with c2: stat_card("Urgent",            str(len(summary["urgent_cases"])), "🔴", "#ef4444")
with c3: stat_card("Overdue Follow-Up", str(len(summary["overdue_cases"])),"⏰", "#f59e0b")
with c4: stat_card("Missing Docs",      str(summary["missing_docs"]),      "📄", "#f59e0b")
with c5: stat_card("Closed",            str(summary["closed_count"]),      "✅", "#10b981")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

left, right = st.columns([3, 2], gap="large")

# ── Left: Activity feed ───────────────────────────────────────────────────────
with left:
    st.markdown("""<div style="font-size:1.05rem;font-weight:700;margin-bottom:14px;">
    📋 Recent Activity</div>""", unsafe_allow_html=True)

    activity = query.recent_activity(limit=10)
    if activity:
        for f in activity:
            icon = followup_type_icon(f.get("followup_type", "call"))
            type_colors = {"call":"#6366f1","visit":"#10b981","message":"#f59e0b","email":"#3b82f6"}
            c = type_colors.get(f.get("followup_type","call"), "#6366f1")
            preview = f["note_text"][:110] + ("…" if len(f["note_text"]) > 110 else "")
            blocker_html = (
                f'<div style="color:#f59e0b;font-size:0.78rem;margin-top:4px;">🚧 {f["blockers"][:70]}</div>'
                if f.get("blockers") else ""
            )
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);
            border-left:3px solid {c};border-radius:10px;padding:12px 16px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <div>
                  <span style="font-weight:600;color:rgba(255,255,255,0.9);">{f['student_name']}</span>
                  <span style="color:#6b7280;font-size:0.82rem;margin-left:8px;">{icon} {f['worker_name']}</span>
                </div>
                <span style="color:#6b7280;font-size:0.75rem;">{fmt_datetime(f['date'])[:12]}</span>
              </div>
              <div style="color:#9ca3af;font-size:0.85rem;line-height:1.5;">{preview}</div>
              {blocker_html}
            </div>""", unsafe_allow_html=True)
    else:
        empty_state("📋", "No activity yet",
                    "Run: python seed/demo_seed.py to load demo data",
                    "Then add follow-ups to see the activity feed here")

# ── Right: AI Briefing + Urgent + Quick Actions ───────────────────────────────
with right:
    # AI Daily Briefing
    st.markdown("""<div style="font-size:1.05rem;font-weight:700;margin-bottom:14px;">
    🧠 AI Daily Briefing</div>""", unsafe_allow_html=True)

    active_cases = storage.list_cases(status="active")
    if not active_cases:
        empty_state("📁", "No active cases", "Add cases to see AI briefings")
    elif not cognee_svc.cognee_available():
        st.warning("Configure Cognee Cloud to enable AI briefings.", icon="🔑")
    else:
        if st.button("✨ Generate Today's Briefing", type="primary", use_container_width=True):
            with st.spinner("Asking Cognee what needs your attention today..."):
                briefing = cognee_svc.recall_urgent_context(
                    [c["case_id"] for c in active_cases],
                    cases=active_cases,
                )
            ai_insight_box("Today's Priorities", briefing)
            st.session_state["last_briefing"] = briefing
        elif "last_briefing" in st.session_state:
            ai_insight_box("Today's Priorities", st.session_state["last_briefing"])

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Urgent cases
    st.markdown("""<div style="font-size:1.05rem;font-weight:700;margin-bottom:10px;">
    🔥 Needs Attention</div>""", unsafe_allow_html=True)

    urgent = summary["urgent_cases"]
    if urgent:
        for c in urgent[:4]:
            lbl = query.urgency_label(c)
            from utils.helpers import urgency_css, fmt_date
            tc, bg, border = urgency_css(lbl)
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};border-radius:10px;
            padding:10px 14px;margin-bottom:6px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <span style="font-weight:600;color:rgba(255,255,255,0.9);">{c['student_name']}</span>
                  <span style="color:#6b7280;font-size:0.78rem;margin-left:6px;">
                  👤 {c['assigned_volunteer']}</span>
                </div>
                <span style="color:{tc};font-size:0.78rem;font-weight:700;">{lbl}</span>
              </div>
              <div style="color:#6b7280;font-size:0.78rem;margin-top:3px;">
              📅 {fmt_date(c['deadline'])}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);
        border-radius:10px;padding:14px;text-align:center;color:#10b981;font-weight:600;">
        🎉 No urgent cases right now!
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Quick actions
    st.markdown("""<div style="font-size:1.05rem;font-weight:700;margin-bottom:10px;">
    ⚡ Quick Actions</div>""", unsafe_allow_html=True)
    st.page_link("pages/1_Add_Case.py",       label="➕ Register new case",      icon="📁")
    st.page_link("pages/2_Add_Followup.py",   label="📝 Log a follow-up",        icon="📞")
    st.page_link("pages/3_Case_Detail.py",    label="🗂️ View / edit a case",     icon="🔍")
    st.page_link("pages/4_Ask_ThreadTrace.py", label="💬 Ask the AI assistant",   icon="🧠")
    st.page_link("pages/5_Search.py",         label="🔎 Search cases",           icon="🔎")
    st.page_link("pages/6_Dashboard.py",      label="📊 Full dashboard",         icon="📈")
    st.page_link("pages/7_Reports.py",        label="📋 Reports & export",       icon="📋")
    st.page_link("pages/8_Close_Purge.py",    label="🗑️ Close / purge a case",   icon="🗂️")
