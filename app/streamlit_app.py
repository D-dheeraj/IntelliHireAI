import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Initialize Database ───────────────────────────────────────────────────────
from database.connection import engine
from models.base import Base
from models.candidate import Candidate
from models.job import Job
from models.application import Application
from models.skill import Skill
from models.agent_log import AgentLog

Base.metadata.create_all(bind=engine)

from services.query_service import get_candidates
from services.database_service import delete_candidate, delete_all_candidates
from dashboards.dashboard import candidate_chart, match_chart
from services.pdf_service import extract_text
from agents.manager_agent import run_intellihire
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="IntelliHire AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════════════════════
# BASE CSS — applied on every page
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Nuke all Streamlit chrome ── */
#MainMenu, footer,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton,
[data-testid="collapsedControl"]
{ display: none !important; visibility: hidden !important; height: 0 !important; }

/* ── Base ── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, sans-serif;
}

.stApp { background: #f1f5f9 !important; }

/* ── Kill default top padding ── */
.block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
}

/* ── Input fields ── */
.stTextInput input {
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.65rem 0.9rem !important;
    background: #f8fafc !important;
    color: #0f172a !important;
}
.stTextInput input:focus {
    border-color: #6366f1 !important;
    background: white !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
.stTextInput label { display: none !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.01em !important;
    transition: all 0.18s ease !important;
    border: none !important;
    padding: 0.65rem 1.4rem !important;
}
button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important;
}
button[kind="secondary"] {
    background: white !important;
    border: 1.5px solid #e2e8f0 !important;
    color: #374151 !important;
}
button[kind="secondary"]:hover {
    border-color: #6366f1 !important;
    color: #6366f1 !important;
    background: #f5f3ff !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f172a !important;
    min-width: 240px !important;
    max-width: 240px !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div { color: #94a3b8 !important; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
    gap: 2px !important;
}
[data-testid="stSidebar"] .stRadio label {
    border-radius: 8px !important;
    padding: 0.55rem 0.8rem !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
    transition: all 0.15s !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: #1e293b !important;
    color: white !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9; border-radius: 10px; padding: 4px; gap: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #0f172a !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #c7d2fe !important;
    border-radius: 12px !important;
    background: #fafafe !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #374151 !important;
    border-radius: 10px !important;
}

/* ── Alerts ── */
.stAlert { border-radius: 10px !important; font-size: 0.85rem !important; }

/* ── Progress ── */
.stProgress > div > div { background: #6366f1 !important; }

/* ── Misc ── */
hr { border-color: #e2e8f0 !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

def _creds():
    u = os.getenv("ADMIN_USERNAME", "admin")
    p = os.getenv("ADMIN_PASSWORD", "intellihire2026")
    try:
        u = st.secrets.get("ADMIN_USERNAME", u)
        p = st.secrets.get("ADMIN_PASSWORD", p)
    except Exception:
        pass
    return u, p

def _check_admin(u, p):
    au, ap = _creds()
    return u.strip() == au and p == ap

def _logout():
    st.session_state.pop("role", None)
    st.session_state.pop("admin_error", None)
    st.rerun()

def _has_api_key():
    k = os.getenv("GEMINI_API_KEY", "")
    if not k:
        try: k = st.secrets.get("GEMINI_API_KEY", "")
        except: pass
    return bool(k and k.strip())

# ── Score / pill helpers ───────────────────────────────────────────────────────
def sc(s):
    if s >= 70: return "#059669", "#d1fae5"
    if s >= 40: return "#d97706", "#fef3c7"
    return "#dc2626", "#fee2e2"

def rec_colors(r):
    m = {"Strong Hire":("#065f46","#d1fae5"), "Hire":("#1e40af","#dbeafe"),
         "Maybe":("#92400e","#fef3c7"), "No Hire":("#991b1b","#fee2e2")}
    return m.get(r, ("#92400e","#fef3c7"))

def skill_tags(lst, bg="#f1f5f9", col="#475569", border="#e2e8f0"):
    if not lst: return ""
    items = lst if isinstance(lst, list) else [s.strip() for s in lst.split(",") if s.strip()]
    return " ".join(
        f'<span style="display:inline-block;background:{bg};color:{col};'
        f'border:1px solid {border};border-radius:6px;padding:2px 10px;'
        f'font-size:0.74rem;font-weight:500;margin:2px;">{s}</span>'
        for s in items if s
    )


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════

def show_login():
    # Full dark background override
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(160deg, #0f172a 0%, #1a2744 55%, #0f1f3d 100%) !important;
    }
    .block-container { padding: 0 !important; margin: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    # --- Brand header (full width, no card) ---
    st.markdown("""
    <div style="padding: 3.5rem 0 2rem; text-align: center;">
        <div style="display:inline-flex;align-items:center;gap:14px;margin-bottom:0.6rem;">
            <div style="width:50px;height:50px;
                background:linear-gradient(135deg,#6366f1,#8b5cf6);
                border-radius:14px;display:flex;align-items:center;
                justify-content:center;font-size:1.2rem;font-weight:800;
                color:white;letter-spacing:-0.5px;
                box-shadow:0 8px 24px rgba(99,102,241,0.4);">
                IH
            </div>
            <div style="font-size:1.9rem;font-weight:800;color:white;letter-spacing:-0.5px;">
                IntelliHire<span style="color:#818cf8;">AI</span>
            </div>
        </div>
        <div style="font-size:0.85rem;color:#64748b;letter-spacing:0.04em;">
            Intelligent Resume Screening Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Login card (centered) ---
    _, col, _ = st.columns([1, 1.1, 1])

    with col:
        # Candidate section
        st.markdown("""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
            border-radius:16px;padding:1.5rem 1.6rem;margin-bottom:1rem;">
            <div style="font-size:0.65rem;font-weight:700;color:#475569;
                text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.9rem;">
                For Candidates
            </div>
            <div style="font-size:1rem;font-weight:700;color:white;margin-bottom:0.35rem;">
                Analyze My Resume
            </div>
            <div style="font-size:0.82rem;color:#94a3b8;line-height:1.6;">
                Upload your resume and receive an AI-powered match score against
                any job description. No account required.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Continue as Candidate", use_container_width=True,
                     key="btn_guest", type="secondary"):
            st.session_state["role"] = "candidate"
            st.rerun()

        # Divider
        st.markdown("""
        <div style="display:flex;align-items:center;gap:12px;margin:1.2rem 0;">
            <div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>
            <div style="font-size:0.7rem;font-weight:600;color:#334155;">OR</div>
            <div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>
        </div>
        """, unsafe_allow_html=True)

        # Admin section
        st.markdown("""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
            border-radius:16px;padding:1.5rem 1.6rem;margin-bottom:1.2rem;">
            <div style="font-size:0.65rem;font-weight:700;color:#475569;
                text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.9rem;">
                For Recruiters
            </div>
            <div style="font-size:1rem;font-weight:700;color:white;margin-bottom:0.35rem;">
                Recruiter Dashboard
            </div>
            <div style="font-size:0.82rem;color:#94a3b8;line-height:1.6;">
                Full access to candidate analytics, batch resume screening,
                and hiring pipeline management.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.text_input("Username", key="lg_user", placeholder="Username")
        st.text_input("Password", type="password", key="lg_pass",
                      placeholder="Password")

        if st.session_state.get("admin_error"):
            st.markdown("""
            <div style="background:#2d1515;border:1px solid #7f1d1d;border-radius:8px;
                padding:0.7rem 1rem;font-size:0.82rem;color:#fca5a5;margin-bottom:0.5rem;">
                Incorrect username or password.
            </div>
            """, unsafe_allow_html=True)

        if st.button("Sign in as Recruiter", use_container_width=True,
                     key="btn_admin", type="primary"):
            if _check_admin(st.session_state.get("lg_user",""),
                            st.session_state.get("lg_pass","")):
                st.session_state["role"] = "admin"
                st.session_state.pop("admin_error", None)
                st.rerun()
            else:
                st.session_state["admin_error"] = True
                st.rerun()

        st.markdown("""
        <div style="text-align:center;margin-top:2rem;
            font-size:0.72rem;color:#334155;letter-spacing:0.02em;">
            Powered by Google Gemini &nbsp;·&nbsp; FastMCP &nbsp;·&nbsp; Python
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CANDIDATE VIEW
# ══════════════════════════════════════════════════════════════════════════════

def _page_header(title, sub):
    st.markdown(f"""
    <div style="background:white;border-bottom:1px solid #e2e8f0;
        padding:1.2rem 1.8rem;margin:-1rem -1rem 1.8rem -1rem;">
        <div style="font-size:1.2rem;font-weight:700;color:#0f172a;
            letter-spacing:-0.3px;">{title}</div>
        <div style="font-size:0.8rem;color:#64748b;margin-top:3px;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def _sec(label):
    st.markdown(f"""
    <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;
        text-transform:uppercase;letter-spacing:0.12em;
        margin:1.6rem 0 0.7rem;padding-bottom:0.5rem;
        border-bottom:1px solid #f1f5f9;">{label}</div>
    """, unsafe_allow_html=True)


def show_candidate():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.5rem 1rem 1rem;">
            <div style="font-size:1.1rem;font-weight:800;color:white;
                letter-spacing:-0.3px;margin-bottom:6px;">
                IntelliHire<span style="color:#818cf8;">AI</span>
            </div>
            <span style="display:inline-block;background:#0c4a6e;color:#7dd3fc;
                border-radius:6px;padding:2px 10px;font-size:0.65rem;
                font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">
                Candidate
            </span>
        </div>
        <hr style="border-color:#1e293b;margin:0 1rem 1rem;">
        <div style="padding:0.5rem 1rem;font-size:0.8rem;color:#475569;line-height:1.9;">
            What you get:<br>
            · AI match score (0–100)<br>
            · Skill gap breakdown<br>
            · Professional summary<br>
            · Hire recommendation
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1e293b;margin:1rem;'>", unsafe_allow_html=True)
        if st.button("Back to Home", key="c_out", use_container_width=True):
            _logout()

    if not _has_api_key():
        st.error("API key not configured. Contact the administrator.")
        st.stop()

    _page_header("Resume Analyzer", "Get your AI-powered match score against any job description")

    st.markdown("""
    <div style="background:#f0f9ff;border:1px solid #bae6fd;border-left:4px solid #0284c7;
        border-radius:10px;padding:0.85rem 1.1rem;font-size:0.82rem;color:#0369a1;
        margin-bottom:1.5rem;">
        <strong>Privacy:</strong> Your results are saved for recruiter review only.
        Other candidates cannot see your data.
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        _sec("Upload Your Resume")
        f = st.file_uploader("PDF", type="pdf", label_visibility="collapsed",
                             key="c_file")
        if f: st.success(f"Ready: {f.name}")
    with c2:
        _sec("Job Description")
        job = st.text_area("Job", height=155, label_visibility="collapsed",
                           key="c_job",
                           placeholder="Paste the full job description here...")

    if not (f and job):
        st.markdown("""
        <div style="text-align:center;padding:2.5rem;color:#94a3b8;font-size:0.88rem;">
            Upload your resume and paste a job description above to begin.
        </div>""", unsafe_allow_html=True)
        return

    if st.button("Analyze My Resume", type="primary",
                 use_container_width=True, key="c_run"):
        os.makedirs("uploads", exist_ok=True)
        fp = os.path.join("uploads", f.name)
        with open(fp, "wb") as fh: fh.write(f.getbuffer())

        with st.spinner("Analyzing resume — this takes about 20 seconds..."):
            try:
                res = run_intellihire(extract_text(fp), job)
                _render_result(res, f.name)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                with st.expander("Details"): st.exception(e)


def _render_result(result, filename):
    """Shared result renderer for both candidate and admin views."""
    resume = result["resume"]
    skills = result["skills"]
    match  = result["match"]

    name     = resume.get("name") or filename
    score    = match.get("match_score", 0)
    rec      = match.get("recommendation", "Maybe")
    missing  = match.get("missing_skills", [])
    matched  = match.get("matched_skills", [])
    sk_list  = skills.get("skills_list", [])

    fg, bg = sc(score)
    rfg, rbg = rec_colors(rec)

    _sec("Results")

    # Top info bar
    st.markdown(f"""
    <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
        padding:1.4rem 1.6rem;margin-bottom:1rem;
        box-shadow:0 1px 3px rgba(0,0,0,0.05);
        display:flex;justify-content:space-between;align-items:center;">
        <div>
            <div style="font-size:1.05rem;font-weight:700;color:#0f172a;
                margin-bottom:5px;">{name}</div>
            <div style="font-size:0.78rem;color:#94a3b8;line-height:1.9;">
                {resume.get('email','—')} &nbsp;·&nbsp;
                {resume.get('phone','—')} &nbsp;·&nbsp;
                {resume.get('experience','—')} &nbsp;·&nbsp;
                {resume.get('education','—')}
            </div>
        </div>
        <div style="text-align:right;flex-shrink:0;margin-left:2rem;">
            <div style="font-size:2.6rem;font-weight:800;color:{fg};
                letter-spacing:-2px;line-height:1;">
                {score}<span style="font-size:1rem;font-weight:500;">%</span>
            </div>
            <div style="margin-top:6px;">
                <span style="display:inline-block;background:{rbg};color:{rfg};
                    border-radius:100px;padding:4px 14px;font-size:0.78rem;
                    font-weight:600;">{rec}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["Summary", "Skills", "Job Match"])

    with t1:
        st.markdown(f"""
        <div style="font-size:0.9rem;color:#374151;line-height:1.85;padding:0.5rem 0;">
            {resume.get('ai_summary','—')}
        </div>""", unsafe_allow_html=True)

    with t2:
        if sk_list:
            st.markdown(skill_tags(sk_list), unsafe_allow_html=True)
        else:
            st.write(skills.get("skills_text","—"))

    with t3:
        st.markdown(f"""
        <div style="font-size:0.88rem;color:#374151;line-height:1.75;
            margin-bottom:1.2rem;">{match.get('match_summary','—')}</div>
        """, unsafe_allow_html=True)

        cm, cg = st.columns(2)
        with cm:
            if matched:
                st.markdown(f"""
                <div style="font-size:0.68rem;font-weight:700;color:#059669;
                    text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">
                    Matched Skills</div>
                {skill_tags(matched, '#f0fdf4','#166534','#bbf7d0')}
                """, unsafe_allow_html=True)
        with cg:
            if missing:
                st.markdown(f"""
                <div style="font-size:0.68rem;font-weight:700;color:#dc2626;
                    text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">
                    Skill Gaps</div>
                {skill_tags(missing,'#fff1f2','#9f1239','#fecdd3')}
                """, unsafe_allow_html=True)

        st.plotly_chart(match_chart(score), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN VIEW
# ══════════════════════════════════════════════════════════════════════════════

def show_admin():
    all_c  = get_candidates()
    total  = len(all_c)
    hired  = sum(1 for c in all_c if c.recommendation in ("Strong Hire","Hire"))
    avg    = round(sum(c.match_score or 0 for c in all_c)/total) if total else 0

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:1.5rem 1rem 1rem;">
            <div style="font-size:1.1rem;font-weight:800;color:white;
                letter-spacing:-0.3px;margin-bottom:6px;">
                IntelliHire<span style="color:#818cf8;">AI</span>
            </div>
            <span style="display:inline-block;background:#312e81;color:#a5b4fc;
                border-radius:6px;padding:2px 10px;font-size:0.65rem;
                font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">
                Recruiter
            </span>
        </div>
        <hr style="border-color:#1e293b;margin:0 1rem 0.5rem;">
        """, unsafe_allow_html=True)

        page = st.radio("nav",
                        ["Analyze Resumes","Dashboard","All Candidates"],
                        label_visibility="collapsed")

        st.markdown(f"""
        <hr style="border-color:#1e293b;margin:0.5rem 1rem;">
        <div style="padding:0.75rem 1rem;">
            <div style="background:#1e293b;border-radius:10px;padding:0.8rem 1rem;
                margin-bottom:0.5rem;">
                <div style="font-size:0.65rem;font-weight:700;color:#475569;
                    text-transform:uppercase;letter-spacing:0.08em;">Total</div>
                <div style="font-size:1.5rem;font-weight:800;color:white;">{total}</div>
            </div>
            <div style="background:#1e293b;border-radius:10px;padding:0.8rem 1rem;
                margin-bottom:0.5rem;">
                <div style="font-size:0.65rem;font-weight:700;color:#475569;
                    text-transform:uppercase;letter-spacing:0.08em;">Recommended</div>
                <div style="font-size:1.5rem;font-weight:800;color:#a5b4fc;">{hired}</div>
            </div>
            <div style="background:#1e293b;border-radius:10px;padding:0.8rem 1rem;">
                <div style="font-size:0.65rem;font-weight:700;color:#475569;
                    text-transform:uppercase;letter-spacing:0.08em;">Avg Score</div>
                <div style="font-size:1.5rem;font-weight:800;color:#a5b4fc;">{avg}%</div>
            </div>
        </div>
        <hr style="border-color:#1e293b;margin:0.5rem 1rem;">
        """, unsafe_allow_html=True)

        if total > 0:
            with st.expander("Danger Zone", expanded=False):
                st.warning("Permanently deletes all candidate records.")
                if st.button("Delete All", type="secondary",
                             key="del_all", use_container_width=True):
                    delete_all_candidates()
                    st.rerun()

        if st.button("Sign Out", key="a_out", use_container_width=True):
            _logout()

    if not _has_api_key():
        st.error("GEMINI_API_KEY not configured. Add it to Streamlit Secrets.")
        st.stop()

    # ── Analyze Resumes ───────────────────────────────────────────────────────
    if page == "Analyze Resumes":
        _page_header("Batch Resume Screening",
                     "Upload multiple resumes and screen against a job description")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            _sec("Resume Files")
            files = st.file_uploader("PDFs", type="pdf",
                                     accept_multiple_files=True,
                                     label_visibility="collapsed",
                                     key="a_files")
            if files:
                st.success(f"{len(files)} file(s) selected")
        with c2:
            _sec("Job Description")
            job = st.text_area("Job", height=155, label_visibility="collapsed",
                               key="a_job",
                               placeholder="Paste job description here...")

        if not (files and job):
            st.markdown("""
            <div style="text-align:center;padding:2.5rem;color:#94a3b8;font-size:0.88rem;">
                Select resume files and enter a job description to begin.
            </div>""", unsafe_allow_html=True)
            return

        if st.button("Screen All Resumes", type="primary",
                     use_container_width=True, key="a_run"):
            os.makedirs("uploads", exist_ok=True)
            prog = st.progress(0, text="Starting...")
            for i, f in enumerate(files):
                prog.progress(i/len(files), text=f"Processing {f.name}...")
                fp = os.path.join("uploads", f.name)
                with open(fp,"wb") as fh: fh.write(f.getbuffer())
                with st.spinner(f"Screening {f.name}..."):
                    try:
                        res = run_intellihire(extract_text(fp), job)
                        with st.expander(
                            f"{res['resume'].get('name') or f.name}  ·  "
                            f"{res['match'].get('match_score',0)}%  ·  "
                            f"{res['match'].get('recommendation','Maybe')}",
                            expanded=True
                        ):
                            _render_result(res, f.name)
                    except Exception as e:
                        st.error(f"Failed: {f.name} — {e}")
            prog.progress(1.0, text="Done!")

    # ── Dashboard ─────────────────────────────────────────────────────────────
    elif page == "Dashboard":
        _page_header("Analytics Dashboard", "Overview of all screened candidates")

        cands = get_candidates()
        if not cands:
            st.info("No candidates yet. Go to Analyze Resumes first.")
            return

        n     = len(cands)
        hire  = sum(1 for c in cands if c.recommendation in ("Strong Hire","Hire"))
        maybe = sum(1 for c in cands if c.recommendation == "Maybe")
        no    = sum(1 for c in cands if c.recommendation == "No Hire")
        avg_s = round(sum(c.match_score or 0 for c in cands)/n)
        top   = max(cands, key=lambda c: c.match_score or 0)

        def mcard(label, val, color="#0f172a"):
            return f"""
            <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;
                padding:1.1rem 1.2rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:0.65rem;font-weight:700;color:#94a3b8;
                    text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">
                    {label}</div>
                <div style="font-size:1.9rem;font-weight:800;color:{color};
                    letter-spacing:-1px;">{val}</div>
            </div>"""

        m1,m2,m3,m4,m5 = st.columns(5)
        m1.markdown(mcard("Total",n), unsafe_allow_html=True)
        m2.markdown(mcard("Recommended",hire,"#059669"), unsafe_allow_html=True)
        m3.markdown(mcard("Maybe",maybe,"#d97706"), unsafe_allow_html=True)
        m4.markdown(mcard("No Hire",no,"#dc2626"), unsafe_allow_html=True)
        m5.markdown(mcard("Avg Score",f"{avg_s}%","#6366f1"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ch, ct = st.columns([2.2,1], gap="large")
        with ch:
            _sec("Match Score Comparison")
            st.plotly_chart(candidate_chart(cands), use_container_width=True)
        with ct:
            _sec("Top Candidate")
            tfg,tbg = sc(top.match_score or 0)
            rfg,rbg = rec_colors(top.recommendation or "")
            st.markdown(f"""
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
                padding:1.5rem;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:0.8rem;">
                    {top.name or '—'}</div>
                <div style="font-size:2.4rem;font-weight:800;color:{tfg};letter-spacing:-1px;">
                    {top.match_score or 0}<span style="font-size:1rem;">%</span></div>
                <div style="margin:8px 0 1rem;">
                    <span style="background:{rbg};color:{rfg};border-radius:100px;
                        padding:4px 14px;font-size:0.78rem;font-weight:600;">
                        {top.recommendation or '—'}</span>
                </div>
                <div style="font-size:0.78rem;color:#64748b;line-height:1.6;text-align:left;">
                    {(top.ai_summary[:140]+'…') if top.ai_summary and len(top.ai_summary)>140 else top.ai_summary or '—'}
                </div>
            </div>""", unsafe_allow_html=True)

        _sec("Candidate List")
        f1,f2,f3 = st.columns([2,1.5,1.5])
        with f1:
            fil = st.multiselect("Rec","Strong Hire Hire Maybe No Hire".split(),
                                 default="Strong Hire Hire Maybe No Hire".split(),
                                 label_visibility="collapsed")
        with f2:
            minscore = st.slider("Min",0,100,0)
        with f3:
            srt = st.selectbox("Sort",["Score ↓","Score ↑","Name A–Z"],
                               label_visibility="collapsed")

        filtered = [c for c in cands
                    if (c.recommendation or "Maybe") in fil
                    and (c.match_score or 0) >= minscore]
        if srt == "Score ↓": filtered.sort(key=lambda c: c.match_score or 0, reverse=True)
        elif srt == "Score ↑": filtered.sort(key=lambda c: c.match_score or 0)
        else: filtered.sort(key=lambda c: c.name or "")

        st.markdown(f'<div style="font-size:0.78rem;color:#94a3b8;margin-bottom:0.75rem;">'
                    f'Showing {len(filtered)} of {n}</div>', unsafe_allow_html=True)

        for c in filtered:
            cfg,cbg = sc(c.match_score or 0)
            rfg,rbg = rec_colors(c.recommendation or "")
            with st.expander(f"{c.name or 'Unknown'}  ·  {c.match_score or 0}%  ·  {c.recommendation or '—'}"):
                l,r = st.columns([3,1])
                with l:
                    st.markdown(f"""
                    <div style="font-size:0.78rem;color:#94a3b8;line-height:2;margin-bottom:0.75rem;">
                        {c.email or '—'} · {c.phone or '—'} · {c.experience or '—'} · {c.education or '—'}
                    </div>
                    <div style="font-size:0.87rem;color:#374151;line-height:1.7;margin-bottom:0.75rem;">
                        {c.ai_summary or '—'}</div>
                    {skill_tags(c.skills.split(',') if c.skills else [])}
                    """, unsafe_allow_html=True)
                with r:
                    st.markdown(f"""
                    <div style="text-align:center;padding:0.75rem;">
                        <div style="font-size:2.2rem;font-weight:800;color:{cfg};letter-spacing:-1px;">
                            {c.match_score or 0}<span style="font-size:0.9rem;">%</span></div>
                        <div style="margin-top:6px;">
                            <span style="background:{rbg};color:{rfg};border-radius:100px;
                                padding:4px 12px;font-size:0.75rem;font-weight:600;">
                                {c.recommendation or '—'}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if st.button("Remove", key=f"d_{c.candidate_id}",
                                 use_container_width=True):
                        delete_candidate(c.candidate_id); st.rerun()

    # ── All Candidates ────────────────────────────────────────────────────────
    elif page == "All Candidates":
        _page_header("All Candidates", "Complete candidate database")

        cands = get_candidates()
        if not cands:
            st.info("No candidates yet."); return

        # Header row
        st.markdown("""
        <div style="display:grid;grid-template-columns:2fr 1fr 1.2fr 0.6fr;
            gap:1rem;padding:0.4rem 1.2rem;
            font-size:0.65rem;font-weight:700;color:#94a3b8;
            text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">
            <div>Candidate</div><div>Score</div>
            <div>Recommendation</div><div></div>
        </div>""", unsafe_allow_html=True)

        for c in sorted(cands, key=lambda x: x.match_score or 0, reverse=True):
            cfg,_ = sc(c.match_score or 0)
            rfg,rbg = rec_colors(c.recommendation or "")
            n1,n2,n3,n4 = st.columns([2,1,1.2,0.6])
            with n1:
                st.markdown(f"""
                <div style="padding:0.65rem 0;">
                    <div style="font-size:0.9rem;font-weight:600;color:#0f172a;">
                        {c.name or 'Unknown'}</div>
                    <div style="font-size:0.74rem;color:#94a3b8;margin-top:2px;">
                        {c.email or '—'} · {c.experience or '—'}</div>
                </div>""", unsafe_allow_html=True)
            with n2:
                st.markdown(f"""
                <div style="padding:0.75rem 0;font-size:1.25rem;font-weight:800;color:{cfg};">
                    {c.match_score or 0}%</div>""", unsafe_allow_html=True)
            with n3:
                st.markdown(f"""
                <div style="padding:0.85rem 0;">
                    <span style="background:{rbg};color:{rfg};border-radius:100px;
                        padding:4px 14px;font-size:0.76rem;font-weight:600;">
                        {c.recommendation or '—'}</span>
                </div>""", unsafe_allow_html=True)
            with n4:
                if st.button("Remove", key=f"t_{c.candidate_id}",
                             use_container_width=True):
                    delete_candidate(c.candidate_id); st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
role = st.session_state.get("role")

if   role is None:      show_login()
elif role == "candidate": show_candidate()
elif role == "admin":     show_admin()