import streamlit as st
from src.ui.upload_page import show_upload_page
from src.ui.results_page import show_results_page

st.set_page_config(
    page_title="HireMe — AI Career Co-Pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global premium CSS ─────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400&display=swap');

      /* ── Base ── */
      html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
      }
      .stApp {
        background: radial-gradient(ellipse 80% 60% at 50% -10%, #1e1b4b22, transparent),
                    #020817;
      }
      .block-container {
        max-width: 960px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
      }

      /* ── Tabs ── */
      .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #0f172a;
        border-radius: 14px;
        padding: 5px;
        border: 1px solid #1e293b;
      }
      .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 600;
        font-size: 13px;
        padding: 8px 16px;
        color: #64748b;
        transition: all .2s;
      }
      .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #312e81, #4c1d95) !important;
        color: #e0e7ff !important;
      }

      /* ── File uploader ── */
      [data-testid="stFileUploader"] > div {
        border: 2px dashed #334155 !important;
        border-radius: 14px !important;
        background: #0f172a !important;
        transition: border-color .2s;
      }
      [data-testid="stFileUploader"] > div:hover {
        border-color: #6366f1 !important;
      }

      /* ── Metrics ── */
      [data-testid="stMetric"] {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 18px 20px;
        text-align: center;
      }
      [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
      }

      /* ── Status box ── */
      [data-testid="stStatusWidget"] {
        background: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        font-family: 'Inter', monospace !important;
        font-size: 13px !important;
      }

      /* ── Expander ── */
      [data-testid="stExpander"] {
        background: #0f172a;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
      }
      [data-testid="stExpander"] summary {
        font-weight: 600;
        color: #94a3b8;
      }

      /* ── Divider ── */
      hr { border-color: #1e293b !important; margin: 1.5rem 0; }

      /* ── Text area ── */
      .stTextArea textarea {
        background: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
        color: #cbd5e1 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        line-height: 1.7 !important;
      }
      .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px #6366f120 !important;
      }

      /* ── Select box ── */
      [data-testid="stSelectbox"] > div > div {
        background: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
      }

      /* ── Text input ── */
      [data-testid="stTextInput"] input {
        background: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-size: 14px !important;
      }
      [data-testid="stTextInput"] input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px #6366f120 !important;
      }

      /* ── Buttons ── */
      .stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        transition: all .2s ease !important;
        border: 1px solid #334155 !important;
        background: #0f172a !important;
        color: #e2e8f0 !important;
      }
      /* Main CTA button — the big launch one */
      .stButton > button[data-testid*="launch"],
      div[data-testid="column"] .stButton > button:not([disabled]) {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        border: none !important;
        color: white !important;
        padding: 14px !important;
        font-size: 16px !important;
        letter-spacing: .3px !important;
      }
      .stButton > button:not([disabled]):hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px #6366f144 !important;
      }
      .stButton > button[disabled] {
        opacity: 0.4 !important;
      }

      /* ── Link buttons ── */
      [data-testid="stLinkButton"] a {
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        transition: all .2s !important;
      }
      [data-testid="stLinkButton"] a:hover {
        border-color: #6366f1 !important;
        color: #818cf8 !important;
      }

      /* ── Scrollbar ── */
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-track { background: #0f172a; }
      ::-webkit-scrollbar-thumb { background: #334155; border-radius: 99px; }
      ::-webkit-scrollbar-thumb:hover { background: #475569; }

      /* ── Caption ── */
      .stCaption { color: #475569 !important; font-size: 12px !important; }

      /* ── Warning / success ── */
      [data-testid="stAlert"] {
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
        background: #0f172a !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state defaults ─────────────────────────────────────────────────────
_DEFAULTS = {
    "stage":     "upload",
    "cv_data":   None,
    "results":   [],
    "roadmap":   {},
    "location":  "",
    "count":     3,
    "error":     None,
    "last_file": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Route ──────────────────────────────────────────────────────────────────────
if st.session_state.stage == "upload":
    show_upload_page()
elif st.session_state.stage == "results":
    show_results_page()
