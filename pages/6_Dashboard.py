import streamlit as st
from services import storage_service as storage
from services import cognee_service as cognee_svc
from services import query_service as query
from utils.helpers import (
    cognee_status_banner, fmt_date, fmt_datetime,
    followup_type_icon, ai_insight_box, stat_card, urgency_css, empty_state,
)
from utils.styles import inject_styles

st.set_page_config(page_title="Dashboard | ThreadTrace", page_icon="📊", layout="wide")
inject_styles()

st.markdown("""
<h1 style="margin-bottom:4px;">📊 Dashboard</h1>
<p style="color:#6b7280;margin-bottom:20px;">Live caseload overview with AI-powered insights</p>
""", unsafe_allow_html=True)
cognee_status_banner()

summary = query.dashboard_summary()

# ── Metrics ───────────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
with m1: stat_card("Active Cases",      str(summary["active_count"]),       "📁", "#6366f1")
with m2: stat_card("Urgent",            str(len(summary["urgent_cases"])),  "🔴", "#ef4444")
with m3: stat_card("Overdue Follow-Up", str(len(summary["overdue_cases"])), "⏰", "#f59e0b")
with m4: stat_card("Missing Docs",      str(summary["missing_docs"]),       "📄", "#f59e0b")
with m5: stat_card("Closed",            str(summary["closed_count"]),       "✅", "#10b981")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

tab_ov, tab_vol, tab_act, tab_ai = st.tabs(
    ["📋 Overview", "👥 Volunteers", "📰 Activity Feed", "🧠 AI Briefing"])

# ══════════ TAB 1: Overview ══════════
with tab_ov:
    col_u, col_d = st.columns(2, gap="large")

    with col_u:
        st.markdown("#### 🔴 Urgent Cases")
        urgent = summary["urgent_cases"]
        if urgent:
            for c in urgent:
                lbl = query.urgency_label(c)
                tc, bg, br = urgency_css(lbl)
                st.markdown(f"""
                <div style="background:{bg};border:1px solid {br};
                border-radius:12px;padding:14px 18px;margin-bottom:8px;">
                  <div style="font-weight:700;margin-bottom:4px;">{c['student_name']}
                    <code style="font-size:0.7rem;color:#6b7280;margin-left:6px;">{c['case_id']}</code>
                  </div>
                  <div style="font-size:0.82rem;color:#9ca3af;">
                    📅 {fmt_date(c['deadline'])} &nbsp;·&nbsp; 👤 {c['assigned_volunteer']}
                    &nbsp;·&nbsp; <span style="color:{tc};font-weight:600;">{lbl}</span>
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);
            border-radius:12px;padding:18px;text-align:center;color:#10b981;font-weight:600;">
            🎉 No urgent cases!
            </div>""", unsafe_allow_html=True)

    with col_d:
        st.markdown("#### 📅 Deadlines")
        overdue  = query.cases_deadline_overdue()
        thisweek = query.cases_with_deadline_this_week()
        if overdue:
            st.markdown("**⛔ Deadline passed**")
            for c in overdue:
                st.error(
                    f"**{c['student_name']}** — {fmt_date(c['deadline'])} — {c['assigned_volunteer']}")
        if thisweek:
            st.markdown("**🔴 Due this week**")
            for c in thisweek:
                d = query.days_until(c["deadline"])
                st.warning(
                    f"**{c['student_name']}** — {fmt_date(c['deadline'])} ({d}d) — {c['assigned_volunteer']}")
        if not overdue and not thisweek:
            st.success("No immediate deadlines this week.")

    st.divider()
    st.markdown("#### ⏰ Overdue Follow-Ups")
    overdue_fup = summary["overdue_cases"]
    if overdue_fup:
        rows = []
        for c in overdue_fup:
            last = storage.last_followup_date(c["case_id"])
            days = query.days_since_followup(c["case_id"])
            rows.append({
                "Student":        c["student_name"],
                "Location":       c["location"],
                "Volunteer":      c["assigned_volunteer"],
                "Last Follow-Up": last.isoformat() if last else "Never",
                "Days Ago":       days if days is not None else "—",
                "Deadline":       fmt_date(c["deadline"]),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.success("All cases followed up recently. ✅")

# ══════════ TAB 2: Volunteers ══════════
with tab_vol:
    st.markdown("#### 👥 Volunteer Workload")
    workload = query.volunteer_workload()
    if not workload:
        empty_state("👥", "No active cases", "Add cases to see volunteer workload")
    else:
        st.dataframe([{
            "Volunteer":          w["volunteer"],
            "Active Cases":       w["cases"],
            "Urgent":             w["urgent"],
            "Overdue Follow-Up":  w["overdue"],
        } for w in workload], use_container_width=True, hide_index=True)

        st.divider()
        for w in workload:
            vol_cases = storage.list_cases(status="active", volunteer=w["volunteer"])
            tag = ""
            if w["urgent"]:  tag += f" 🔴 {w['urgent']} urgent"
            if w["overdue"]: tag += f" 🟡 {w['overdue']} overdue"
            with st.expander(f"**{w['volunteer']}** — {w['cases']} cases{tag}"):
                for c in vol_cases:
                    lbl = query.urgency_label(c)
                    cc1, cc2, cc3 = st.columns([3, 2, 2])
                    cc1.markdown(f"**{c['student_name']}** `{c['case_id']}`")
                    cc2.caption(f"📅 {fmt_date(c['deadline'])}")
                    cc3.caption(lbl)

        if cognee_svc.cognee_available():
            st.divider()
            if st.button("🧠 AI Volunteer Workload Insights", use_container_width=True):
                active_ids = [c["case_id"] for c in storage.list_cases(status="active")]
                with st.spinner("Analyzing volunteer workload from memory..."):
                    insight = cognee_svc.recall_across_cases(
                        "For each volunteer, what are the most critical things they need "
                        "to do right now? Which volunteer's cases have the most unresolved "
                        "blockers? Who needs support?", active_ids)
                ai_insight_box("Volunteer Workload Intelligence", insight)

# ══════════ TAB 3: Activity Feed ══════════
with tab_act:
    st.markdown("#### 📰 Recent Activity")
    activity = query.recent_activity(limit=30)
    if not activity:
        empty_state("📰", "No activity yet", "Log follow-ups to see the activity feed")
    else:
        workers  = sorted({f["worker_name"] for f in activity})
        worker_f = st.selectbox("Filter by worker", ["All"] + workers)
        filtered = activity if worker_f == "All" else [
            f for f in activity if f["worker_name"] == worker_f]

        type_colors = {"call":"#6366f1","visit":"#10b981","message":"#f59e0b","email":"#3b82f6"}
        for f in filtered:
            icon  = followup_type_icon(f.get("followup_type", "call"))
            color = type_colors.get(f.get("followup_type", "call"), "#6366f1")
            preview = f["note_text"][:180] + ("…" if len(f["note_text"]) > 180 else "")
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.025);
            border:1px solid rgba(255,255,255,0.07);border-left:3px solid {color};
            border-radius:10px;padding:12px 16px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                <div>
                  <span style="font-weight:600;">{f['student_name']}</span>
                  <span style="color:#6b7280;font-size:0.82rem;margin-left:8px;">
                    {icon} {f.get('followup_type','call').title()} by {f['worker_name']}</span>
                </div>
                <span style="color:#6b7280;font-size:0.78rem;">{fmt_datetime(f['date'])[:10]}</span>
              </div>
              <div style="color:#9ca3af;font-size:0.85rem;">{preview}</div>
              {"<div style='color:#f59e0b;font-size:0.8rem;margin-top:4px;'>🚧 " + f['blockers'] + "</div>" if f.get('blockers') else ""}
              {"<div style='color:#818cf8;font-size:0.8rem;margin-top:2px;'>➡️ " + f['next_step'] + "</div>" if f.get('next_step') else ""}
            </div>""", unsafe_allow_html=True)

# ══════════ TAB 4: AI Briefing ══════════
with tab_ai:
    st.markdown("#### 🧠 AI-Powered Briefing")
    active_ids = [c["case_id"] for c in storage.list_cases(status="active")]

    if not cognee_svc.cognee_available():
        st.warning("Configure Cognee Cloud to enable AI briefings.", icon="🔑")
    elif not active_ids:
        empty_state("📁", "No active cases", "Add cases to generate briefings")
    else:
        ca, cb = st.columns(2, gap="large")
        briefings = {
            "🔥 Today's Priority Cases": (
                "What are the most urgent things needing immediate attention today? "
                "Name specific students and the exact action required.", "dash_priority"),
            "🚧 Common Blockers": (
                "What are the most common and recurring blockers across all cases? "
                "Group by type. Which are most urgent?", "dash_blockers"),
            "⚠️ At-Risk Cases": (
                "Which cases are most at risk of the student not achieving their goal? "
                "Consider deadline proximity, unresolved blockers, gaps in follow-up. "
                "Name students specifically.", "dash_atrisk"),
            "📋 Full Caseload Summary": (
                "Analyze all cases and provide: 1) most common blockers, "
                "2) cases needing urgent attention, 3) patterns in missing documents, "
                "4) one concrete recommendation to improve outcomes.", "dash_insights"),
        }
        items = list(briefings.items())
        for col, (name, (q, key)) in zip([ca, ca, cb, cb], items):
            with col:
                if st.button(name, use_container_width=True,
                             type="primary" if key == "dash_priority" else "secondary"):
                    with st.spinner(f"Generating: {name}..."):
                        result = cognee_svc.recall_across_cases(q, active_ids)
                    st.session_state[key] = result
                if key in st.session_state:
                    ai_insight_box(name, st.session_state[key])
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
