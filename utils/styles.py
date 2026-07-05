"""
utils/styles.py — Global CSS for ThreadTrace.

Injected once per page via inject_styles().
Design system: dark-accented cards, indigo/violet gradient brand,
clean typography, consistent spacing, expressive status colors.
"""

STYLES = """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Root variables ── */
:root {
    --brand-primary:   #6366f1;
    --brand-secondary: #8b5cf6;
    --brand-gradient:  linear-gradient(135deg, #6366f1, #8b5cf6);
    --success:         #10b981;
    --warning:         #f59e0b;
    --danger:          #ef4444;
    --muted:           #6b7280;
    --card-bg:         rgba(255,255,255,0.04);
    --card-border:     rgba(255,255,255,0.08);
    --radius:          12px;
    --radius-sm:       8px;
}

/* ── Global font ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Sidebar styling ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
}
section[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.85) !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label {
    color: rgba(255,255,255,0.6) !important;
    font-size: 0.8rem !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 16px 20px !important;
    transition: transform 0.2s, box-shadow 0.2s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(99,102,241,0.15);
}
[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: var(--brand-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
}
.stButton > button[kind="primary"] {
    background: var(--brand-gradient) !important;
    border: none !important;
    color: white !important;
}

/* ── Form inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border-radius: var(--radius-sm) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--brand-primary) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 4px;
    border: 1px solid var(--card-border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--brand-gradient) !important;
    color: white !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
}

/* ── Containers with border ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: var(--radius) !important;
    border: 1px solid var(--card-border) !important;
    background: var(--card-bg) !important;
    transition: box-shadow 0.2s;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
    box-shadow: 0 4px 16px rgba(99,102,241,0.1);
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1px solid var(--card-border) !important;
}

/* ── Alerts / status boxes ── */
.stAlert {
    border-radius: var(--radius-sm) !important;
    border: none !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(99,102,241,0.15) !important;
    margin: 24px 0 !important;
}

/* ── Page title styling ── */
h1 {
    font-weight: 700 !important;
    background: var(--brand-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
}
h2 { font-weight: 600 !important; }
h3 { font-weight: 600 !important; }

/* ── Download button ── */
.stDownloadButton > button {
    background: var(--brand-gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: var(--brand-primary) !important;
}

/* ── Page link ── */
.stPageLink a {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--card-border) !important;
    padding: 10px 16px !important;
    transition: all 0.2s !important;
    background: var(--card-bg) !important;
    display: block !important;
    font-weight: 500 !important;
    margin-bottom: 6px !important;
}
.stPageLink a:hover {
    border-color: var(--brand-primary) !important;
    background: rgba(99,102,241,0.08) !important;
    transform: translateX(4px) !important;
}

/* ── Radio buttons ── */
.stRadio label {
    cursor: pointer;
}
</style>
"""


def inject_styles():
    """Call once at the top of every page."""
    import streamlit as st
    st.markdown(STYLES, unsafe_allow_html=True)
