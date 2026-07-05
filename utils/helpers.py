"""
utils/helpers.py — Shared UI components for ThreadTrace.
"""
import json
import streamlit as st
from datetime import datetime, date
from services import cognee_service as cognee_svc
from services import query_service as query


# ── Cognee banner ─────────────────────────────────────────────────────────────

def cognee_status_banner():
    if cognee_svc.cognee_available():
        st.markdown(
            '<div style="background:linear-gradient(90deg,rgba(99,102,241,0.15),rgba(139,92,246,0.1));'
            'border:1px solid rgba(99,102,241,0.3);border-radius:10px;padding:10px 16px;'
            'display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
            '<span style="font-size:1.1rem">🧠</span>'
            '<span style="font-weight:600;color:#818cf8;">Cognee Cloud connected</span>'
            '<span style="color:#6b7280;font-size:0.88rem;">— AI memory features active</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);'
            'border-radius:10px;padding:10px 16px;display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
            '<span style="font-size:1.1rem">🔑</span>'
            '<span style="font-weight:600;color:#f59e0b;">Cognee not configured</span>'
            '<span style="color:#6b7280;font-size:0.88rem;">— Set COGNEE_BASE_URL + COGNEE_API_KEY in .env</span>'
            '</div>',
            unsafe_allow_html=True,
        )


def cognee_guard() -> bool:
    if not cognee_svc.cognee_available():
        st.markdown(
            '<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);'
            'border-radius:10px;padding:14px 18px;text-align:center;">'
            '<div style="font-size:1.5rem;margin-bottom:6px;">🔑</div>'
            '<div style="font-weight:600;color:#f59e0b;">Cognee Cloud not configured</div>'
            '<div style="color:#6b7280;font-size:0.88rem;margin-top:4px;">'
            'Add COGNEE_BASE_URL and COGNEE_API_KEY to your .env file</div></div>',
            unsafe_allow_html=True,
        )
        return False
    return True


# ── status helpers ────────────────────────────────────────────────────────────

DOC_STATUS_COLORS = {
    "submitted":            "🟢",
    "missing":              "🔴",
    "pending_verification": "🟡",
}
DOC_STATUS_CSS = {
    "submitted":            ("#10b981", "rgba(16,185,129,0.12)"),
    "missing":              ("#ef4444", "rgba(239,68,68,0.12)"),
    "pending_verification": ("#f59e0b", "rgba(245,158,11,0.12)"),
}
FOLLOWUP_TYPE_ICONS = {
    "call":    "📞",
    "visit":   "🏠",
    "message": "💬",
    "email":   "📧",
}

def doc_status_badge(status: str) -> str:
    color, bg = DOC_STATUS_CSS.get(status, ("#6b7280", "rgba(107,114,128,0.1)"))
    label = status.replace("_", " ").title()
    return (
        f'<span style="background:{bg};color:{color};border:1px solid {color}40;'
        f'border-radius:20px;padding:2px 10px;font-size:0.78rem;font-weight:600;">'
        f'{DOC_STATUS_COLORS.get(status,"⚪")} {label}</span>'
    )

def followup_type_icon(ftype: str) -> str:
    return FOLLOWUP_TYPE_ICONS.get(ftype, "📝")

def urgency_color(label: str) -> str:
    if "⛔" in label or "Overdue" in label: return "error"
    if "🔴" in label: return "error"
    if "🟡" in label: return "warning"
    if "🟢" in label: return "success"
    if "✅" in label: return "success"
    return "info"

def urgency_css(label: str) -> tuple:
    """Returns (text_color, bg_color, border_color) for custom badge."""
    if "⛔" in label or ("Overdue" in label and "🟡" not in label):
        return "#ef4444", "rgba(239,68,68,0.12)", "rgba(239,68,68,0.3)"
    if "🔴" in label:
        return "#ef4444", "rgba(239,68,68,0.12)", "rgba(239,68,68,0.3)"
    if "🟡" in label:
        return "#f59e0b", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.3)"
    if "🟢" in label or "✅" in label:
        return "#10b981", "rgba(16,185,129,0.12)", "rgba(16,185,129,0.3)"
    return "#6366f1", "rgba(99,102,241,0.12)", "rgba(99,102,241,0.3)"


# ── date helpers ──────────────────────────────────────────────────────────────

def fmt_date(iso_str: str) -> str:
    if not iso_str:
        return "—"
    try:
        return datetime.fromisoformat(iso_str).strftime("%b %d, %Y")
    except Exception:
        return iso_str[:10]

def fmt_datetime(iso_str: str) -> str:
    if not iso_str:
        return "—"
    try:
        return datetime.fromisoformat(iso_str).strftime("%b %d, %Y · %I:%M %p")
    except Exception:
        return iso_str

def days_label(n: int) -> str:
    if n == 0: return "today"
    if n == 1: return "tomorrow"
    if n < 0:  return f"{abs(n)}d overdue"
    return f"in {n} days"


# ── AI insight box ────────────────────────────────────────────────────────────

# def ai_insight_box(title: str, content: str):
#     # Escape HTML special chars in content
#     safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
#     st.markdown(
#         f"""<div style="background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(139,92,246,0.06));
#         border:1px solid rgba(99,102,241,0.25);border-left:4px solid #6366f1;
#         border-radius:12px;padding:18px 22px;margin:10px 0;">
#         <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
#           <span style="font-size:1.1rem;">🧠</span>
#           <span style="font-weight:700;color:#818cf8;font-size:0.95rem;
#           text-transform:uppercase;letter-spacing:0.04em;">{title}</span>
#         </div>
#         <div style="color:rgba(255,255,255,0.85);font-size:0.93rem;line-height:1.7;
#         white-space:pre-wrap;">{safe}</div>
#         </div>""",
#         unsafe_allow_html=True,
#     )


import json
import streamlit as st


def ai_insight_box(title: str, content: str):
    # -----------------------------
    # Parse Cognee response
    # -----------------------------
    try:
        responses = json.loads(content)
    except Exception:
        st.warning(content)
        return

    # -----------------------------
    # Extract actual JSON from each dataset
    # -----------------------------
    items = []

    for response in responses:

        text = response.get("text", "")

        if not text:
            continue

        try:
            parsed = json.loads(text)

            if isinstance(parsed, list):
                items.extend(parsed)
            else:
                items.append(parsed)

        except Exception:
            continue

    if not items:
        st.info("No urgent items found.")
        return

    # -----------------------------
    # Merge duplicate students
    # -----------------------------
    priority_order = {
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    merged = {}

    for item in items:

        student = item.get("student", "Unknown")

        if student not in merged:

            merged[student] = {
                "student": student,
                "priority": item.get("priority", "LOW").upper(),
                "deadline": item.get("deadline", ""),
                "issues": [],
                "actions": [],
            }

        current = merged[student]

        # Keep highest priority
        if priority_order.get(item.get("priority", "LOW").upper(), 1) > \
           priority_order.get(current["priority"], 1):

            current["priority"] = item.get("priority", "LOW").upper()

        # Keep first deadline if available
        if not current["deadline"]:
            current["deadline"] = item.get("deadline", "")

        issue = item.get("issue", "").strip()
        action = item.get("action", "").strip()

        if issue and issue not in current["issues"]:
            current["issues"].append(issue)

        if action and action not in current["actions"]:
            current["actions"].append(action)

    items = list(merged.values())

    # -----------------------------
    # Sort by priority
    # -----------------------------
    items.sort(
        key=lambda x: priority_order.get(x["priority"], 1),
        reverse=True,
    )

    # -----------------------------
    # Title
    # -----------------------------
    st.markdown(
        f"""
<div style="margin-bottom:16px;">
<span style="
font-size:1rem;
font-weight:700;
color:#818cf8;
letter-spacing:0.05em;
text-transform:uppercase;">
🧠 {title}
</span>
</div>
""",
        unsafe_allow_html=True,
    )

    # -----------------------------
    # Colors
    # -----------------------------
    priority_colors = {
        "HIGH": "#ef4444",
        "MEDIUM": "#facc15",
        "LOW": "#22c55e",
    }

    priority_icons = {
        "HIGH": "🔴",
        "MEDIUM": "🟡",
        "LOW": "🟢",
    }

    # -----------------------------
    # Cards
    # -----------------------------
    for item in items:

        priority = item["priority"]

        color = priority_colors.get(priority, "#22c55e")
        icon = priority_icons.get(priority, "🟢")

        deadline_html = ""

        if item["deadline"]:
            deadline_html = f"""
<div style="
color:#fca5a5;
font-size:0.88rem;
margin-bottom:12px;">
📅 Deadline: {item["deadline"]}
</div>
"""

        issues_html = "".join(
            f"<li>{issue}</li>"
            for issue in item["issues"]
        )

        actions_html = "".join(
            f"<li>{action}</li>"
            for action in item["actions"]
        )

        st.markdown(
            f"""
<div style="
background:#111827;
border:1px solid rgba(255,255,255,0.08);
border-left:6px solid {color};
border-radius:14px;
padding:18px;
margin-bottom:16px;
">

<div style="
color:{color};
font-size:0.9rem;
font-weight:700;
margin-bottom:10px;">
{icon} {priority}
</div>

<div style="
font-size:1.15rem;
font-weight:700;
color:white;
margin-bottom:10px;">
👤 {item["student"]}
</div>

{deadline_html}

<div style="
color:#d1d5db;
margin-bottom:6px;
font-weight:600;">
📄 Issues
</div>

<ul style="
color:#d1d5db;
margin-top:4px;
margin-bottom:14px;
padding-left:20px;">
{issues_html}
</ul>

<div style="
color:#9ca3af;
font-weight:600;
margin-bottom:6px;">
➡ Next Actions
</div>

<ul style="
color:#9ca3af;
padding-left:20px;
margin-top:4px;">
{actions_html}
</ul>

</div>
""",
            unsafe_allow_html=True,
        )

# ── stat card ─────────────────────────────────────────────────────────────────

def stat_card(label: str, value: str, icon: str = "", color: str = "#6366f1", delta: str = ""):
    delta_html = (
        f'<div style="font-size:0.75rem;color:#10b981;margin-top:2px;">{delta}</div>'
        if delta else ""
    )
    _html = (
        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
        f'border-radius:12px;padding:18px 20px;text-align:center;">'
        f'<div style="font-size:1.6rem;margin-bottom:4px;">{icon}</div>'
        f'<div style="font-size:2rem;font-weight:700;background:linear-gradient(135deg,{color},{color}aa);'
        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{value}</div>'
        f'<div style="font-size:0.75rem;font-weight:600;color:#6b7280;'
        f'text-transform:uppercase;letter-spacing:0.05em;margin-top:4px;">{label}</div>'
        f'{delta_html}</div>'
    )
    st.markdown(_html, unsafe_allow_html=True)


# ── section header ────────────────────────────────────────────────────────────

def section_header(title: str, subtitle: str = ""):
    sub_html = (
        f'<p style="color:#6b7280;font-size:0.88rem;margin:2px 0 0 0;">{subtitle}</p>'
        if subtitle else ""
    )
    _sh = (
        f'<div style="margin:20px 0 12px 0;">' +
        f'<h3 style="margin:0;font-weight:700;font-size:1.1rem;">{title}</h3>' +
        f'{sub_html}</div>'
    )
    st.markdown(_sh, unsafe_allow_html=True)


# ── case card ─────────────────────────────────────────────────────────────────

def render_case_card(case: dict, show_ai_summary: bool = False):
    label   = query.urgency_label(case)
    tc, bg, border = urgency_css(label)
    missing = query.missing_docs_count(case["case_id"])
    ds      = query.days_since_followup(case["case_id"])
    last_fup = f"{ds}d ago" if ds is not None else "Never"

    _missing_span = (
        f'&nbsp;·&nbsp; <span style="color:#ef4444;">📄 {missing} missing</span>'
        if missing else ''
    )
    _card = (
        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
        f'border-radius:14px;padding:18px 22px;margin-bottom:10px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        f'<div style="flex:1;">'
        f'<div style="font-size:1.15rem;font-weight:700;margin-bottom:4px;">'
        f'{case["student_name"]}'
        f'<span style="font-size:0.72rem;color:#6b7280;font-weight:400;margin-left:8px;font-family:monospace;">{case["case_id"]}</span></div>'
        f'<div style="color:#9ca3af;font-size:0.85rem;margin-bottom:6px;">'
        f'📍 {case["location"]} &nbsp;·&nbsp; 🎯 {case["goal"]} &nbsp;·&nbsp; 👤 {case["assigned_volunteer"]}</div>'
        f'<div style="color:#6b7280;font-size:0.82rem;">'
        f'📋 {case["target_program_or_scholarship"]} &nbsp;·&nbsp; 📅 {fmt_date(case["deadline"])} &nbsp;·&nbsp; 🕐 Last contact: {last_fup}'
        f'{_missing_span}</div></div>'
        f'<div style="margin-left:16px;text-align:right;">'
        f'<span style="background:{bg};color:{tc};border:1px solid {border};'
        f'border-radius:20px;padding:4px 12px;font-size:0.78rem;font-weight:700;'
        f'white-space:nowrap;">{label}</span></div></div></div>'
    )
    st.markdown(_card, unsafe_allow_html=True)

    if show_ai_summary and cognee_svc.cognee_available():
        with st.expander("🧠 AI Summary", expanded=False):
            with st.spinner("Recalling from memory..."):
                summary = cognee_svc.summarize_case(case["case_id"], case["student_name"])
            ai_insight_box("Case Summary", summary)


# ── follow-up card ────────────────────────────────────────────────────────────

def render_followup_card(f: dict, show_delete: bool = False):
    icon  = followup_type_icon(f.get("followup_type", "call"))
    ftype = f.get("followup_type", "call").title()
    deleted = False

    type_colors = {
        "call": "#6366f1", "visit": "#10b981",
        "message": "#f59e0b", "email": "#3b82f6",
    }
    color = type_colors.get(f.get("followup_type", "call"), "#6366f1")

    col_main, col_del = st.columns([12, 1]) if show_delete else (st.container(), None)

    with (col_main if show_delete else col_main):
        _blocker_html = (
            f'<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);'
            f'border-radius:8px;padding:8px 12px;font-size:0.83rem;color:#f59e0b;margin-top:6px;">'
            f'🚧 <strong>Blocker:</strong> {f["blockers"]}</div>'
        ) if f.get("blockers") else ""
        _next_html = (
            f'<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);'
            f'border-radius:8px;padding:8px 12px;font-size:0.83rem;color:#818cf8;margin-top:6px;">'
            f'➡️ <strong>Next:</strong> {f["next_step"]}</div>'
        ) if f.get("next_step") else ""
        _date_html = (
            f'<div style="color:#6b7280;font-size:0.78rem;margin-top:6px;">'
            f'📅 Next follow-up: {fmt_date(f["next_followup_date"])}</div>'
        ) if f.get("next_followup_date") else ""
        _note = f["note_text"].replace("\n", "<br>")
        _fup_card = (
            f'<div style="background:rgba(255,255,255,0.025);'
            f'border:1px solid rgba(255,255,255,0.07);border-left:3px solid {color};'
            f'border-radius:12px;padding:16px 20px;margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="background:rgba(255,255,255,0.06);border-radius:6px;'
            f'padding:3px 10px;font-size:0.8rem;font-weight:600;color:{color};">{icon} {ftype}</span>'
            f'<span style="font-weight:600;color:rgba(255,255,255,0.85);">{f["worker_name"]}</span>'
            f'</div>'
            f'<span style="color:#6b7280;font-size:0.8rem;">{fmt_datetime(f["date"])}</span>'
            f'</div>'
            f'<div style="color:rgba(255,255,255,0.75);font-size:0.9rem;line-height:1.6;margin-bottom:8px;">{_note}</div>'
            f'{_blocker_html}{_next_html}{_date_html}'
            f'</div>'
        )
        st.markdown(_fup_card, unsafe_allow_html=True)

    if show_delete and col_del:
        with col_del:
            st.markdown("<div style='padding-top:8px'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_fup_{f['followup_id']}", help="Delete"):
                deleted = True

    return deleted


# ── document table ────────────────────────────────────────────────────────────

def render_document_table(docs: list, editable: bool = False):
    from services import storage_service as storage
    updates = []
    if not docs:
        st.markdown(
            '<div style="text-align:center;padding:24px;color:#6b7280;'
            'border:1px dashed rgba(255,255,255,0.1);border-radius:12px;">'
            '📄 No documents tracked yet</div>',
            unsafe_allow_html=True,
        )
        return updates

    for doc in docs:
        color, bg = DOC_STATUS_CSS.get(doc["status"], ("#6b7280", "rgba(107,114,128,0.1)"))[:2]
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(
                    f"**{doc['doc_name']}**"
                    + (f"\n\n_{doc['notes']}_" if doc.get("notes") else "")
                )
            with col2:
                if editable:
                    new_status = st.selectbox(
                        "Status",
                        storage.VALID_DOC_STATUSES,
                        index=storage.VALID_DOC_STATUSES.index(doc["status"]),
                        key=f"docstatus_{doc['doc_id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != doc["status"]:
                        updates.append((doc["doc_id"], new_status))
                else:
                    st.markdown(
                        doc_status_badge(doc["status"]), unsafe_allow_html=True
                    )
            with col3:
                if editable:
                    if st.button("🗑️", key=f"deldoc_{doc['doc_id']}", help="Remove"):
                        storage.delete_document(doc["doc_id"])
                        st.rerun()
    return updates


# ── empty state ───────────────────────────────────────────────────────────────

def empty_state(icon: str, title: str, subtitle: str = "", action: str = ""):
    action_html = (
        f'<div style="margin-top:8px;color:#6366f1;font-size:0.85rem;">{action}</div>'
        if action else ""
    )
    _es = (
        f'<div style="text-align:center;padding:48px 24px;'
        f'border:1px dashed rgba(99,102,241,0.2);border-radius:16px;'
        f'background:rgba(99,102,241,0.03);">'
        f'<div style="font-size:3rem;margin-bottom:12px;">{icon}</div>'
        f'<div style="font-weight:600;font-size:1.05rem;margin-bottom:6px;">{title}</div>'
        f'<div style="color:#6b7280;font-size:0.88rem;">{subtitle}</div>'
        f'{action_html}</div>'
    )
    st.markdown(_es, unsafe_allow_html=True)
