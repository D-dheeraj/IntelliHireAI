import streamlit as st
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# ── Initialize Database ───────────────────────────────────────────────────────
from database.connection import engine
from models.base import Base
from models.candidate import Candidate
from models.job import Job
from models.application import Application
from models.skill import Skill
from models.agent_log import AgentLog

Base.metadata.create_all(bind=engine)

# ── Imports ───────────────────────────────────────────────────────────────────
from services.query_service import get_candidates
from services.database_service import delete_candidate, delete_all_candidates
from dashboards.dashboard import candidate_chart, match_chart
from services.pdf_service import extract_text
from agents.manager_agent import run_intellihire
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliHire AI — Resume Screening Platform",
    page_icon="https://img.icons8.com/fluency/48/artificial-intelligence.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Fonts & Reset ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

/* ── Global background ── */
.stApp { background: #f1f5f9; }

/* ══════════════════════════════════════════
   LOGIN PAGE
══════════════════════════════════════════ */
.login-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f2350 100%);
    display: flex; align-items: center; justify-content: center;
    padding: 2rem;
}

.login-container {
    width: 100%; max-width: 480px; margin: 0 auto;
}

.login-brand {
    text-align: center; margin-bottom: 2.5rem;
}

.brand-logo {
    display: inline-flex; align-items: center; gap: 12px;
    margin-bottom: 0.75rem;
}

.brand-icon {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; font-weight: 800; color: white;
    letter-spacing: -1px;
}

.brand-name {
    font-size: 1.75rem; font-weight: 800;
    color: white; letter-spacing: -0.5px;
}

.brand-name span { color: #818cf8; }

.login-tagline {
    font-size: 0.9rem; color: #94a3b8; font-weight: 400;
    letter-spacing: 0.02em;
}

.login-card {
    background: white;
    border-radius: 20px;
    padding: 2.5rem;
    box-shadow: 0 25px 50px rgba(0,0,0,0.35);
}

.login-section-title {
    font-size: 0.7rem; font-weight: 700; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.12em;
    margin-bottom: 1rem;
}

.option-card {
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    background: #f8fafc;
    transition: border-color 0.2s, background 0.2s;
}

.option-card:hover { border-color: #6366f1; background: #f5f3ff; }

.option-title {
    font-size: 0.95rem; font-weight: 700; color: #0f172a;
    margin-bottom: 0.25rem;
}

.option-desc {
    font-size: 0.8rem; color: #64748b; line-height: 1.5;
}

.divider-or {
    text-align: center; position: relative;
    margin: 1.5rem 0;
    color: #cbd5e1; font-size: 0.75rem; font-weight: 600;
}

.divider-or::before, .divider-or::after {
    content: ''; position: absolute;
    top: 50%; width: calc(50% - 24px);
    height: 1px; background: #e2e8f0;
}
.divider-or::before { left: 0; }
.divider-or::after  { right: 0; }

/* ── Streamlit input overrides ── */
.stTextInput input {
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 0.9rem !important;
    background: #f8fafc !important;
    transition: border-color 0.2s !important;
}
.stTextInput input:focus {
    border-color: #6366f1 !important;
    background: white !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}

/* ── Buttons ── */
.stButton button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.2s !important;
    letter-spacing: 0.01em !important;
}

.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
}

.stButton button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}

.stButton button[kind="secondary"] {
    background: white !important;
    border: 1.5px solid #e2e8f0 !important;
    color: #374151 !important;
}

.stButton button[kind="secondary"]:hover {
    border-color: #6366f1 !important;
    color: #6366f1 !important;
    background: #f5f3ff !important;
}

/* ══════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #0f172a !important;
    border-right: none !important;
}

[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

.sidebar-brand {
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 1rem;
}

.sidebar-brand-name {
    font-size: 1.15rem; font-weight: 800;
    color: white !important; letter-spacing: -0.3px;
}

.sidebar-brand-name span { color: #818cf8 !important; }

.sidebar-role-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    margin-top: 4px;
}

.badge-admin { background: #312e81; color: #a5b4fc !important; }
.badge-candidate { background: #0c4a6e; color: #7dd3fc !important; }

.sidebar-stat {
    background: #1e293b;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
}

.sidebar-stat-label {
    font-size: 0.7rem; color: #64748b !important;
    text-transform: uppercase; letter-spacing: 0.08em;
}

.sidebar-stat-value {
    font-size: 1.4rem; font-weight: 700;
    color: white !important; line-height: 1.2;
}

/* ── Sidebar radio buttons ── */
[data-testid="stSidebar"] .stRadio label {
    background: transparent !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.75rem !important;
    margin-bottom: 2px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
    transition: all 0.15s !important;
    cursor: pointer !important;
}

[data-testid="stSidebar"] .stRadio label:hover {
    background: #1e293b !important;
    color: white !important;
}

/* ══════════════════════════════════════════
   MAIN CONTENT
══════════════════════════════════════════ */

/* Page header */
.page-header {
    background: white;
    border-bottom: 1px solid #e2e8f0;
    padding: 1.25rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    display: flex; align-items: center; justify-content: space-between;
}

.page-title {
    font-size: 1.3rem; font-weight: 700;
    color: #0f172a; letter-spacing: -0.3px;
}

.page-subtitle { font-size: 0.82rem; color: #64748b; margin-top: 2px; }

/* Section headers */
.section-header {
    font-size: 0.72rem; font-weight: 700; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.12em;
    margin: 2rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e2e8f0;
}

/* Cards */
.card {
    background: white; border-radius: 14px;
    border: 1px solid #e2e8f0;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.card-sm {
    background: white; border-radius: 10px;
    border: 1px solid #e2e8f0;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* Metric cards */
.metric-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
}

.metric-box {
    background: white; border-radius: 12px;
    border: 1px solid #e2e8f0;
    padding: 1.1rem 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.metric-label {
    font-size: 0.7rem; font-weight: 600; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin-bottom: 0.4rem;
}

.metric-value {
    font-size: 1.8rem; font-weight: 800; color: #0f172a;
    letter-spacing: -1px; line-height: 1;
}

.metric-accent { color: #6366f1; }

/* Score display */
.score-ring {
    text-align: center; padding: 1rem;
}

.score-number {
    font-size: 3rem; font-weight: 800;
    letter-spacing: -2px; line-height: 1;
}

.score-high { color: #059669; }
.score-mid  { color: #d97706; }
.score-low  { color: #dc2626; }

/* Recommendation tag */
.rec-pill {
    display: inline-block;
    padding: 4px 14px; border-radius: 100px;
    font-size: 0.78rem; font-weight: 600;
    letter-spacing: 0.02em;
}
.rec-strong-hire { background: #d1fae5; color: #065f46; }
.rec-hire        { background: #dbeafe; color: #1e40af; }
.rec-maybe       { background: #fef3c7; color: #92400e; }
.rec-no-hire     { background: #fee2e2; color: #991b1b; }

/* Skill tags */
.skill-tag {
    display: inline-block;
    background: #f1f5f9; color: #475569;
    border: 1px solid #e2e8f0;
    border-radius: 6px; padding: 2px 10px;
    font-size: 0.75rem; font-weight: 500;
    margin: 2px 2px;
}

.skill-tag-matched {
    background: #f0fdf4; color: #166534;
    border-color: #bbf7d0;
}

.skill-tag-missing {
    background: #fff1f2; color: #9f1239;
    border-color: #fecdd3;
}

/* Candidate row */
.candidate-row {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.4rem;
    margin-bottom: 0.6rem;
    display: flex; align-items: center;
    transition: border-color 0.15s, box-shadow 0.15s;
}

.candidate-row:hover {
    border-color: #c7d2fe;
    box-shadow: 0 2px 8px rgba(99,102,241,0.08);
}

.candidate-name {
    font-size: 0.95rem; font-weight: 600; color: #0f172a;
}

.candidate-meta {
    font-size: 0.78rem; color: #94a3b8; margin-top: 2px;
}

/* Info banner */
.info-banner {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-left: 4px solid #0284c7;
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    font-size: 0.85rem; color: #0369a1;
    margin-bottom: 1.5rem;
}

/* Upload zone */
[data-testid="stFileUploader"] {
    border: 2px dashed #c7d2fe !important;
    border-radius: 12px !important;
    background: #f5f3ff !important;
    transition: border-color 0.2s !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: #6366f1 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0; background: #f1f5f9;
    border-radius: 10px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #0f172a !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
}

/* Progress bar */
.stProgress .st-bo { background: #6366f1 !important; }

/* Alert overrides */
.stAlert {
    border-radius: 10px !important;
    border: none !important;
    font-size: 0.85rem !important;
}

/* Expander */
.streamlit-expanderHeader {
    border-radius: 10px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}

hr { border-color: #e2e8f0 !important; margin: 1.5rem 0 !important; }

.footer-note {
    text-align: center;
    font-size: 0.72rem; color: #94a3b8;
    margin-top: 2rem; padding-top: 1rem;
    border-top: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_admin_creds():
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "intellihire2026")
    try:
        username = st.secrets.get("ADMIN_USERNAME", username)
        password = st.secrets.get("ADMIN_PASSWORD", password)
    except Exception:
        pass
    return username, password


def _check_admin(username: str, password: str) -> bool:
    admin_user, admin_pass = _get_admin_creds()
    return username.strip() == admin_user and password == admin_pass


def _logout():
    for key in ["role", "admin_error"]:
        st.session_state.pop(key, None)
    st.rerun()


def _check_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass
    return api_key is not None and len(api_key.strip()) > 0


# ── Score / rec helpers ────────────────────────────────────────────────────────
def score_cls(s):
    if s >= 70: return "score-high"
    if s >= 40: return "score-mid"
    return "score-low"

def rec_pill_cls(r):
    return {
        "Strong Hire": "rec-strong-hire",
        "Hire":        "rec-hire",
        "Maybe":       "rec-maybe",
        "No Hire":     "rec-no-hire",
    }.get(r, "rec-maybe")

def skill_tags(skills_str, cls="skill-tag"):
    if not skills_str: return ""
    return " ".join(
        f'<span class="{cls}">{s.strip()}</span>'
        for s in skills_str.split(",") if s.strip()
    )


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════

def show_login_page():
    # Full-page dark background via CSS
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f2350 100%) !important; }
    .block-container { padding: 3rem 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.4, 1])

    with col:
        # Brand
        st.markdown("""
        <div style="text-align:center; margin-bottom:2.5rem;">
            <div style="display:inline-flex;align-items:center;gap:14px;margin-bottom:0.75rem;">
                <div style="width:52px;height:52px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    border-radius:14px;display:flex;align-items:center;justify-content:center;
                    font-size:1.4rem;font-weight:900;color:white;letter-spacing:-1px;">
                    IH
                </div>
                <div style="font-size:1.9rem;font-weight:800;color:white;letter-spacing:-0.5px;">
                    IntelliHire<span style="color:#818cf8;">AI</span>
                </div>
            </div>
            <div style="font-size:0.88rem;color:#94a3b8;letter-spacing:0.03em;">
                Intelligent Resume Screening Platform
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card
        st.markdown('<div style="background:white;border-radius:20px;padding:2.5rem;box-shadow:0 25px 60px rgba(0,0,0,0.4);">', unsafe_allow_html=True)

        # — Candidate option —
        st.markdown("""
        <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
            letter-spacing:0.12em;margin-bottom:0.9rem;">
            For Candidates
        </div>
        <div style="border:1.5px solid #e2e8f0;border-radius:12px;padding:1.1rem 1.3rem;
            background:#f8fafc;margin-bottom:1rem;">
            <div style="font-size:0.95rem;font-weight:700;color:#0f172a;margin-bottom:0.25rem;">
                Analyze My Resume
            </div>
            <div style="font-size:0.8rem;color:#64748b;line-height:1.5;">
                Upload your resume and get an instant AI-powered match score against any job description.
                No account required.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Continue as Candidate", use_container_width=True,
                     key="btn_guest", type="secondary"):
            st.session_state["role"] = "candidate"
            st.rerun()

        # Divider
        st.markdown("""
        <div style="display:flex;align-items:center;gap:12px;margin:1.5rem 0;">
            <div style="flex:1;height:1px;background:#e2e8f0;"></div>
            <div style="font-size:0.72rem;font-weight:600;color:#cbd5e1;">OR</div>
            <div style="flex:1;height:1px;background:#e2e8f0;"></div>
        </div>
        """, unsafe_allow_html=True)

        # — Admin option —
        st.markdown("""
        <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
            letter-spacing:0.12em;margin-bottom:0.9rem;">
            For Recruiters
        </div>
        <div style="border:1.5px solid #e2e8f0;border-radius:12px;padding:1.1rem 1.3rem;
            background:#f8fafc;margin-bottom:1.2rem;">
            <div style="font-size:0.95rem;font-weight:700;color:#0f172a;margin-bottom:0.25rem;">
                Recruiter Dashboard
            </div>
            <div style="font-size:0.8rem;color:#64748b;line-height:1.5;">
                Access all candidate data, analytics dashboard, batch resume processing,
                and candidate management tools.
            </div>
        </div>
        """, unsafe_allow_html=True)

        admin_user = st.text_input("Username", key="login_user", placeholder="Enter username")
        admin_pass = st.text_input("Password", type="password", key="login_pass",
                                   placeholder="Enter password")

        if st.session_state.get("admin_error"):
            st.error("Incorrect username or password.")

        if st.button("Sign in as Recruiter", use_container_width=True,
                     key="btn_admin", type="primary"):
            if _check_admin(admin_user, admin_pass):
                st.session_state["role"] = "admin"
                st.session_state.pop("admin_error", None)
                st.rerun()
            else:
                st.session_state["admin_error"] = True
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center;margin-top:1.5rem;font-size:0.72rem;color:#475569;">
            Powered by Google Gemini &nbsp;·&nbsp; FastMCP &nbsp;·&nbsp; Built with Python
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CANDIDATE VIEW
# ══════════════════════════════════════════════════════════════════════════════

def show_candidate_view():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-name">IntelliHire<span>AI</span></div>
            <div style="margin-top:6px;">
                <span class="sidebar-role-badge badge-candidate">Candidate</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:0.78rem;color:#64748b;line-height:1.8;padding:0.5rem 0;">
            Upload your resume and paste a job description to receive:<br><br>
            &nbsp;&nbsp;· &nbsp;AI match score (0–100)<br>
            &nbsp;&nbsp;· &nbsp;Skill gap analysis<br>
            &nbsp;&nbsp;· &nbsp;Professional summary<br>
            &nbsp;&nbsp;· &nbsp;Hire recommendation
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("Back to Home", key="cand_logout", use_container_width=True):
            _logout()

    if not _check_api_key():
        st.warning("API key not configured. Please contact the administrator.")
        st.stop()

    # Page header
    st.markdown("""
    <div style="background:white;border-bottom:1px solid #e2e8f0;
        padding:1.4rem 2rem;margin:-1rem -1rem 2rem -1rem;">
        <div style="font-size:1.25rem;font-weight:700;color:#0f172a;letter-spacing:-0.3px;">
            Resume Analyzer
        </div>
        <div style="font-size:0.82rem;color:#64748b;margin-top:3px;">
            Get your AI-powered match score instantly
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-banner">
        <strong>Privacy notice:</strong> Your resume data is stored securely and is only
        visible to authorized recruiters. Other candidates cannot see your results.
    </div>
    """, unsafe_allow_html=True)

    col_up, col_job = st.columns([1, 1], gap="large")

    with col_up:
        st.markdown('<div class="section-header">Resume Upload</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload PDF", type="pdf",
            accept_multiple_files=False,
            label_visibility="collapsed",
            key="cand_upload"
        )
        if uploaded_file:
            st.success(f"Ready: {uploaded_file.name}")

    with col_job:
        st.markdown('<div class="section-header">Job Description</div>', unsafe_allow_html=True)
        job = st.text_area(
            "Job desc", height=160, label_visibility="collapsed",
            placeholder="Paste the full job description here — skills, requirements, responsibilities...",
            key="cand_job"
        )

    if not (uploaded_file and job):
        st.markdown("""
        <div style="text-align:center;padding:2rem;color:#94a3b8;font-size:0.88rem;">
            Upload your resume and paste a job description to get started.
        </div>
        """, unsafe_allow_html=True)
        return

    if st.button("Analyze Resume", type="primary", use_container_width=True, key="cand_analyze"):
        os.makedirs("uploads", exist_ok=True)
        fp = os.path.join("uploads", uploaded_file.name)
        with open(fp, "wb") as fh:
            fh.write(uploaded_file.getbuffer())

        with st.spinner("Analyzing your resume — this takes 15–30 seconds..."):
            try:
                text   = extract_text(fp)
                result = run_intellihire(text, job)

                resume = result["resume"]
                skills = result["skills"]
                match  = result["match"]

                name        = resume.get("name") or uploaded_file.name
                score       = match.get("match_score", 0)
                rec         = match.get("recommendation", "Maybe")
                missing     = match.get("missing_skills", [])
                matched_sk  = match.get("matched_skills", [])
                skills_list = skills.get("skills_list", [])

                sc = score_cls(score)
                rc = rec_pill_cls(rec)

                st.markdown('<div class="section-header">Analysis Results</div>',
                            unsafe_allow_html=True)

                # Candidate info card
                st.markdown(f"""
                <div class="card" style="margin-bottom:1.5rem;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div>
                            <div style="font-size:1.1rem;font-weight:700;color:#0f172a;">
                                {name}
                            </div>
                            <div style="font-size:0.8rem;color:#94a3b8;margin-top:4px;line-height:1.8;">
                                {resume.get('email','—')} &nbsp;·&nbsp;
                                {resume.get('phone','—')} &nbsp;·&nbsp;
                                {resume.get('experience','—')} &nbsp;·&nbsp;
                                {resume.get('education','—')}
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div class="score-number {sc}">{score}<span style="font-size:1rem;font-weight:500;">%</span></div>
                            <div style="margin-top:4px;">
                                <span class="rec-pill {rc}">{rec}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                t1, t2, t3 = st.tabs(["Summary", "Skills", "Job Match"])

                with t1:
                    st.markdown(f"""
                    <div style="font-size:0.9rem;color:#374151;line-height:1.8;padding:0.5rem 0;">
                        {resume.get('ai_summary','—')}
                    </div>
                    """, unsafe_allow_html=True)

                with t2:
                    if skills_list:
                        st.markdown(
                            " ".join(f'<span class="skill-tag">{s}</span>'
                                     for s in skills_list),
                            unsafe_allow_html=True
                        )
                    else:
                        st.write(skills.get("skills_text", "—"))

                with t3:
                    st.markdown(f"""
                    <div style="font-size:0.88rem;color:#374151;line-height:1.7;
                        margin-bottom:1.2rem;">{match.get('match_summary','—')}</div>
                    """, unsafe_allow_html=True)

                    col_m, col_mi = st.columns(2)
                    with col_m:
                        if matched_sk:
                            st.markdown(
                                '<div style="font-size:0.72rem;font-weight:700;color:#059669;'
                                'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">'
                                'Matched Skills</div>' +
                                " ".join(f'<span class="skill-tag skill-tag-matched">{s}</span>'
                                         for s in matched_sk),
                                unsafe_allow_html=True
                            )
                    with col_mi:
                        if missing:
                            st.markdown(
                                '<div style="font-size:0.72rem;font-weight:700;color:#dc2626;'
                                'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">'
                                'Skill Gaps</div>' +
                                " ".join(f'<span class="skill-tag skill-tag-missing">{s}</span>'
                                         for s in missing),
                                unsafe_allow_html=True
                            )

                    st.plotly_chart(match_chart(score), use_container_width=True)

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                with st.expander("Error details"):
                    st.exception(e)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN VIEW
# ══════════════════════════════════════════════════════════════════════════════

def show_admin_view():
    candidates_all = get_candidates()
    total   = len(candidates_all)
    hired   = sum(1 for c in candidates_all if c.recommendation in ("Strong Hire","Hire"))
    avg_sc  = round(sum(c.match_score or 0 for c in candidates_all)/total) if total else 0

    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-name">IntelliHire<span>AI</span></div>
            <div style="margin-top:6px;">
                <span class="sidebar-role-badge badge-admin">Recruiter</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        page = st.radio(
            "nav", ["Analyze Resumes", "Dashboard", "All Candidates"],
            label_visibility="collapsed"
        )

        st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="sidebar-stat">
            <div class="sidebar-stat-label">Total Candidates</div>
            <div class="sidebar-stat-value">{total}</div>
        </div>
        <div class="sidebar-stat">
            <div class="sidebar-stat-label">Recommended</div>
            <div class="sidebar-stat-value" style="color:#a5b4fc !important;">{hired}</div>
        </div>
        <div class="sidebar-stat">
            <div class="sidebar-stat-label">Avg Match Score</div>
            <div class="sidebar-stat-value" style="color:#a5b4fc !important;">{avg_sc}%</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        if total > 0:
            with st.expander("Danger Zone"):
                st.warning("Permanently deletes all candidate records.")
                if st.button("Delete All Records", type="secondary",
                             key="admin_del_all", use_container_width=True):
                    delete_all_candidates()
                    st.success("All records deleted.")
                    st.rerun()

        if st.button("Sign Out", key="admin_logout", use_container_width=True):
            _logout()

    if not _check_api_key():
        st.error("GEMINI_API_KEY is not configured. Add it to your Streamlit Secrets.")
        st.stop()

    # ════════════════════════════════════════════════════════════════════════
    # PAGE: Analyze Resumes
    # ════════════════════════════════════════════════════════════════════════
    if page == "Analyze Resumes":

        st.markdown("""
        <div style="background:white;border-bottom:1px solid #e2e8f0;
            padding:1.4rem 2rem;margin:-1rem -1rem 2rem -1rem;">
            <div style="font-size:1.25rem;font-weight:700;color:#0f172a;letter-spacing:-0.3px;">
                Batch Resume Screening
            </div>
            <div style="font-size:0.82rem;color:#64748b;margin-top:3px;">
                Upload multiple resumes and screen them against a job description simultaneously
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_up, col_job = st.columns([1, 1], gap="large")

        with col_up:
            st.markdown('<div class="section-header">Resume Files</div>',
                        unsafe_allow_html=True)
            uploaded_files = st.file_uploader(
                "Upload PDFs", type="pdf", accept_multiple_files=True,
                label_visibility="collapsed", key="admin_upload"
            )
            if uploaded_files:
                st.success(f"{len(uploaded_files)} file(s) selected")

        with col_job:
            st.markdown('<div class="section-header">Job Description</div>',
                        unsafe_allow_html=True)
            job = st.text_area(
                "Job desc", height=160, label_visibility="collapsed",
                placeholder="Paste the job description — required skills, experience level, responsibilities...",
                key="admin_job"
            )

        if not (uploaded_files and job):
            st.markdown("""
            <div style="text-align:center;padding:2rem;color:#94a3b8;font-size:0.88rem;">
                Select resume files and enter a job description to begin screening.
            </div>
            """, unsafe_allow_html=True)
            return

        if st.button("Screen All Resumes", type="primary",
                     use_container_width=True, key="admin_analyze"):
            os.makedirs("uploads", exist_ok=True)
            file_paths = []
            for f in uploaded_files:
                fp = os.path.join("uploads", f.name)
                with open(fp, "wb") as fh:
                    fh.write(f.getbuffer())
                file_paths.append(fp)

            progress = st.progress(0, text="Initializing...")
            st.markdown('<div class="section-header">Screening Results</div>',
                        unsafe_allow_html=True)

            for i, path in enumerate(file_paths):
                filename = os.path.basename(path)
                progress.progress(i / len(file_paths),
                                  text=f"Processing {filename}...")

                with st.spinner(f"Screening {filename}..."):
                    try:
                        text   = extract_text(path)
                        result = run_intellihire(text, job)

                        resume = result["resume"]
                        skills = result["skills"]
                        match  = result["match"]

                        name    = resume.get("name") or filename
                        score   = match.get("match_score", 0)
                        rec     = match.get("recommendation", "Maybe")
                        missing = match.get("missing_skills", [])
                        matched_sk = match.get("matched_skills", [])
                        skills_list = skills.get("skills_list", [])

                        sc = score_cls(score)
                        rc = rec_pill_cls(rec)

                        # Result card
                        with st.expander(
                            f"{name}  ·  {score}%  ·  {rec}", expanded=True
                        ):
                            left, right = st.columns([3, 1], gap="large")

                            with left:
                                st.markdown(f"""
                                <div style="font-size:0.8rem;color:#94a3b8;
                                    line-height:1.9;margin-bottom:1rem;">
                                    {resume.get('email','—')} &nbsp;·&nbsp;
                                    {resume.get('phone','—')} &nbsp;·&nbsp;
                                    {resume.get('experience','—')} &nbsp;·&nbsp;
                                    {resume.get('education','—')}
                                </div>
                                """, unsafe_allow_html=True)

                                t1, t2, t3 = st.tabs(["Summary","Skills","Job Match"])
                                with t1:
                                    st.write(resume.get("ai_summary","—"))
                                with t2:
                                    if skills_list:
                                        st.markdown(
                                            " ".join(f'<span class="skill-tag">{s}</span>'
                                                     for s in skills_list),
                                            unsafe_allow_html=True
                                        )
                                with t3:
                                    st.write(match.get("match_summary","—"))
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        if matched_sk:
                                            st.markdown(
                                                '<div style="font-size:0.72rem;font-weight:700;'
                                                'color:#059669;text-transform:uppercase;'
                                                'letter-spacing:0.1em;margin-bottom:8px;">'
                                                'Matched</div>' +
                                                " ".join(
                                                    f'<span class="skill-tag skill-tag-matched">'
                                                    f'{s}</span>' for s in matched_sk),
                                                unsafe_allow_html=True
                                            )
                                    with c2:
                                        if missing:
                                            st.markdown(
                                                '<div style="font-size:0.72rem;font-weight:700;'
                                                'color:#dc2626;text-transform:uppercase;'
                                                'letter-spacing:0.1em;margin-bottom:8px;">'
                                                'Gaps</div>' +
                                                " ".join(
                                                    f'<span class="skill-tag skill-tag-missing">'
                                                    f'{s}</span>' for s in missing),
                                                unsafe_allow_html=True
                                            )

                            with right:
                                st.markdown(f"""
                                <div style="text-align:center;padding:1rem;">
                                    <div class="score-number {sc}">{score}<span
                                        style="font-size:1rem;font-weight:500;">%</span></div>
                                    <div style="margin-top:8px;">
                                        <span class="rec-pill {rc}">{rec}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.plotly_chart(match_chart(score),
                                                use_container_width=True)

                    except Exception as e:
                        st.error(f"Failed to process {filename}: {str(e)}")

            progress.progress(1.0, text="All resumes screened.")

    # ════════════════════════════════════════════════════════════════════════
    # PAGE: Dashboard
    # ════════════════════════════════════════════════════════════════════════
    elif page == "Dashboard":

        st.markdown("""
        <div style="background:white;border-bottom:1px solid #e2e8f0;
            padding:1.4rem 2rem;margin:-1rem -1rem 2rem -1rem;">
            <div style="font-size:1.25rem;font-weight:700;color:#0f172a;letter-spacing:-0.3px;">
                Analytics Dashboard
            </div>
            <div style="font-size:0.82rem;color:#64748b;margin-top:3px;">
                Overview of all screened candidates
            </div>
        </div>
        """, unsafe_allow_html=True)

        candidates = get_candidates()

        if not candidates:
            st.info("No candidates yet. Go to Analyze Resumes to get started.")
            return

        total_c = len(candidates)
        hired_c = sum(1 for c in candidates if c.recommendation in ("Strong Hire","Hire"))
        maybe_c = sum(1 for c in candidates if c.recommendation == "Maybe")
        no_c    = sum(1 for c in candidates if c.recommendation == "No Hire")
        avg_c   = round(sum(c.match_score or 0 for c in candidates)/total_c)
        top_c   = max(candidates, key=lambda c: c.match_score or 0)

        # Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f"""<div class="card-sm">
                <div class="metric-label">Total Screened</div>
                <div class="metric-value">{total_c}</div></div>""",
                unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="card-sm">
                <div class="metric-label">Recommended</div>
                <div class="metric-value metric-accent">{hired_c}</div></div>""",
                unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="card-sm">
                <div class="metric-label">Maybe</div>
                <div class="metric-value" style="color:#d97706;">{maybe_c}</div></div>""",
                unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="card-sm">
                <div class="metric-label">No Hire</div>
                <div class="metric-value" style="color:#dc2626;">{no_c}</div></div>""",
                unsafe_allow_html=True)
        with m5:
            st.markdown(f"""<div class="card-sm">
                <div class="metric-label">Avg Score</div>
                <div class="metric-value metric-accent">{avg_c}%</div></div>""",
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_chart, col_top = st.columns([2.2, 1], gap="large")

        with col_chart:
            st.markdown('<div class="section-header">Match Score Comparison</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(candidate_chart(candidates), use_container_width=True)

        with col_top:
            st.markdown('<div class="section-header">Top Candidate</div>',
                        unsafe_allow_html=True)
            sc = score_cls(top_c.match_score or 0)
            rc = rec_pill_cls(top_c.recommendation or "")
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:1rem;font-weight:700;color:#0f172a;
                    margin-bottom:0.75rem;">{top_c.name or '—'}</div>
                <div class="score-number {sc}" style="font-size:2.4rem;">
                    {top_c.match_score or 0}<span
                    style="font-size:0.9rem;font-weight:500;">%</span></div>
                <div style="margin-top:8px;margin-bottom:1rem;">
                    <span class="rec-pill {rc}">{top_c.recommendation or '—'}</span>
                </div>
                <div style="font-size:0.78rem;color:#64748b;line-height:1.6;text-align:left;">
                    {(top_c.ai_summary[:140]+'…') if top_c.ai_summary
                     and len(top_c.ai_summary) > 140 else top_c.ai_summary or '—'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Filter bar
        st.markdown('<div class="section-header">Candidate List</div>',
                    unsafe_allow_html=True)
        f1, f2, f3 = st.columns([2, 1.5, 1.5])
        with f1:
            filter_rec = st.multiselect(
                "Recommendation",
                ["Strong Hire","Hire","Maybe","No Hire"],
                default=["Strong Hire","Hire","Maybe","No Hire"],
                label_visibility="collapsed"
            )
        with f2:
            min_score = st.slider("Min score", 0, 100, 0)
        with f3:
            sort_by = st.selectbox(
                "Sort by", ["Score (High → Low)", "Score (Low → High)", "Name A–Z"],
                label_visibility="collapsed"
            )

        filtered = [
            c for c in candidates
            if (c.recommendation or "Maybe") in filter_rec
            and (c.match_score or 0) >= min_score
        ]
        if sort_by == "Score (High → Low)":
            filtered.sort(key=lambda c: c.match_score or 0, reverse=True)
        elif sort_by == "Score (Low → High)":
            filtered.sort(key=lambda c: c.match_score or 0)
        else:
            filtered.sort(key=lambda c: c.name or "")

        st.markdown(f"""<div style="font-size:0.8rem;color:#94a3b8;margin-bottom:1rem;">
            Showing {len(filtered)} of {total_c} candidates</div>""",
            unsafe_allow_html=True)

        for c in filtered:
            sc = score_cls(c.match_score or 0)
            rc = rec_pill_cls(c.recommendation or "")
            with st.expander(
                f"{c.name or 'Unknown'}  ·  {c.match_score or 0}%  ·  {c.recommendation or '—'}"
            ):
                l, r = st.columns([3, 1])
                with l:
                    st.markdown(f"""
                    <div style="font-size:0.8rem;color:#94a3b8;line-height:2;margin-bottom:0.75rem;">
                        {c.email or '—'} &nbsp;·&nbsp; {c.phone or '—'} &nbsp;·&nbsp;
                        {c.experience or '—'} &nbsp;·&nbsp; {c.education or '—'}
                    </div>
                    <div style="font-size:0.85rem;color:#374151;
                        line-height:1.7;margin-bottom:1rem;">
                        {c.ai_summary or '—'}
                    </div>
                    """, unsafe_allow_html=True)
                    if c.skills:
                        st.markdown(skill_tags(c.skills), unsafe_allow_html=True)
                with r:
                    st.markdown(f"""
                    <div style="text-align:center;padding:0.75rem;">
                        <div class="score-number {sc}" style="font-size:2rem;">
                            {c.match_score or 0}<span style="font-size:0.85rem;">%</span></div>
                        <div style="margin-top:6px;">
                            <span class="rec-pill {rc}">{c.recommendation or '—'}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Delete", key=f"del_{c.candidate_id}",
                                 use_container_width=True):
                        delete_candidate(c.candidate_id)
                        st.success("Deleted.")
                        st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    # PAGE: All Candidates
    # ════════════════════════════════════════════════════════════════════════
    elif page == "All Candidates":

        st.markdown("""
        <div style="background:white;border-bottom:1px solid #e2e8f0;
            padding:1.4rem 2rem;margin:-1rem -1rem 2rem -1rem;">
            <div style="font-size:1.25rem;font-weight:700;color:#0f172a;letter-spacing:-0.3px;">
                All Candidates
            </div>
            <div style="font-size:0.82rem;color:#64748b;margin-top:3px;">
                Complete candidate database
            </div>
        </div>
        """, unsafe_allow_html=True)

        candidates = get_candidates()

        if not candidates:
            st.info("No candidates yet.")
            return

        # Table header
        st.markdown("""
        <div style="display:grid;grid-template-columns:2fr 0.8fr 1fr 0.5fr;
            gap:1rem;padding:0.5rem 1.4rem;
            font-size:0.68rem;font-weight:700;color:#94a3b8;
            text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">
            <div>Candidate</div>
            <div>Score</div>
            <div>Recommendation</div>
            <div></div>
        </div>
        """, unsafe_allow_html=True)

        for c in sorted(candidates, key=lambda x: x.match_score or 0, reverse=True):
            sc = score_cls(c.match_score or 0)
            rc = rec_pill_cls(c.recommendation or "")

            col_name, col_score, col_rec, col_del = st.columns([2, 0.8, 1, 0.5])
            with col_name:
                st.markdown(f"""
                <div style="padding:0.6rem 0;">
                    <div style="font-size:0.9rem;font-weight:600;color:#0f172a;">
                        {c.name or 'Unknown'}</div>
                    <div style="font-size:0.76rem;color:#94a3b8;margin-top:2px;">
                        {c.email or '—'} · {c.experience or '—'}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_score:
                st.markdown(f"""
                <div style="padding:0.6rem 0;">
                    <span class="score-number {sc}"
                        style="font-size:1.3rem;">{c.match_score or 0}%</span>
                </div>
                """, unsafe_allow_html=True)
            with col_rec:
                st.markdown(f"""
                <div style="padding:0.8rem 0;">
                    <span class="rec-pill {rc}">{c.recommendation or '—'}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("Remove", key=f"tbl_{c.candidate_id}",
                             use_container_width=True):
                    delete_candidate(c.candidate_id)
                    st.rerun()

            st.markdown("<hr>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

role = st.session_state.get("role", None)

if role is None:
    show_login_page()
elif role == "candidate":
    show_candidate_view()
elif role == "admin":
    show_admin_view()