import streamlit as st
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from services.query_service import get_candidates
from services.database_service import delete_candidate, delete_all_candidates
from dashboards.dashboard import candidate_chart, match_chart
from services.pdf_service import extract_text
from agents.manager_agent import run_intellihire

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliHire AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem 2rem 1.6rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 1.5rem;
}
.hero h1 { font-size: 2.2rem; font-weight: 700; margin: 0; }
.hero p  { font-size: 1rem; margin: 0.4rem 0 0; opacity: 0.88; }

.section-title {
    font-size: 1.1rem; font-weight: 600; color: #4f46e5;
    border-left: 4px solid #4f46e5; padding-left: 10px;
    margin: 1.4rem 0 0.8rem;
}

.result-card {
    background: #f8f7ff; border: 1px solid #e0e7ff;
    border-radius: 12px; padding: 1.1rem 1.4rem; margin-bottom: 0.8rem;
}

.skill-pill {
    display: inline-block; background: #ede9fe; color: #5b21b6;
    border-radius: 20px; padding: 3px 11px;
    font-size: 0.76rem; font-weight: 500; margin: 2px 2px;
}

.score-badge {
    font-size: 2.6rem; font-weight: 700; text-align: center;
    padding: 0.9rem; border-radius: 12px; margin-bottom: 0.4rem;
}
.score-high { background:#d1fae5; color:#065f46; }
.score-mid  { background:#fef3c7; color:#92400e; }
.score-low  { background:#fee2e2; color:#991b1b; }

.rec-tag {
    display: inline-block; padding: 4px 14px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 600;
}
.rec-strong { background:#d1fae5; color:#065f46; }
.rec-hire   { background:#dbeafe; color:#1e40af; }
.rec-maybe  { background:#fef3c7; color:#92400e; }
.rec-no     { background:#fee2e2; color:#991b1b; }

.metric-card {
    background: white; border: 1px solid #e5e7eb; border-radius: 12px;
    padding: 1rem 1.2rem; text-align: center;
}
.metric-card .num { font-size: 2rem; font-weight: 700; color: #4f46e5; }
.metric-card .lbl { font-size: 0.82rem; color: #6b7280; margin-top: 2px; }

.divider { border: none; border-top: 1px solid #e5e7eb; margin: 1.2rem 0; }

[data-testid="stFileUploader"] {
    border: 2px dashed #c4b5fd !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def score_class(s):
    if s >= 70: return "score-high"
    if s >= 40: return "score-mid"
    return "score-low"

def rec_class(r):
    return {"Strong Hire":"rec-strong","Hire":"rec-hire",
            "Maybe":"rec-maybe","No Hire":"rec-no"}.get(r,"rec-maybe")

def skill_pills(skills_str):
    if not skills_str: return ""
    return " ".join(
        f'<span class="skill-pill">{s.strip()}</span>'
        for s in skills_str.split(",") if s.strip()
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 IntelliHire AI")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["🔍 Analyze Resumes", "📊 Dashboard", "🗂 All Candidates"],
        label_visibility="collapsed"
    )
    st.markdown("---")

    candidates_all = get_candidates()
    total   = len(candidates_all)
    hired   = sum(1 for c in candidates_all if c.recommendation in ("Strong Hire","Hire"))
    avg_sc  = round(sum(c.match_score or 0 for c in candidates_all) / total) if total else 0

    st.markdown(f"**📁 Total Candidates:** {total}")
    st.markdown(f"**✅ Recommended:** {hired}")
    st.markdown(f"**📈 Avg Score:** {avg_sc}%")
    st.markdown("---")

    if total > 0:
        with st.expander("⚠️ Danger Zone"):
            st.warning("This will delete ALL candidates from the database.")
            if st.button("🗑 Delete All Candidates", type="secondary"):
                delete_all_candidates()
                st.success("All records deleted.")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Analyze Resumes
# ══════════════════════════════════════════════════════════════════════════════
if page == "🔍 Analyze Resumes":

    st.markdown("""
    <div class="hero">
        <h1>🧠 IntelliHire AI</h1>
        <p>Upload resumes + enter a job description → AI ranks and scores every candidate instantly.</p>
    </div>
    """, unsafe_allow_html=True)

    col_up, col_job = st.columns([1,1], gap="large")

    with col_up:
        st.markdown('<div class="section-title">📤 Upload Resumes</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Drop PDFs here", type="pdf",
            accept_multiple_files=True, label_visibility="collapsed"
        )
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) ready")

    with col_job:
        st.markdown('<div class="section-title">📋 Job Description</div>', unsafe_allow_html=True)
        job = st.text_area(
            "Job desc", height=170, label_visibility="collapsed",
            placeholder="e.g. Looking for a Python developer with REST API, SQL, Docker experience..."
        )

    analyze_btn = st.button(
        "🔍  Analyze Resumes", type="primary",
        use_container_width=True,
        disabled=not (uploaded_files and job)
    )

    if not (uploaded_files and job):
        st.info("👆 Upload at least one PDF and enter a job description to begin.")

    if analyze_btn and uploaded_files and job:
        os.makedirs("uploads", exist_ok=True)

        file_paths = []
        for f in uploaded_files:
            fp = os.path.join("uploads", f.name)
            with open(fp, "wb") as fh:
                fh.write(f.getbuffer())
            file_paths.append(fp)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 Analysis Results</div>', unsafe_allow_html=True)

        progress = st.progress(0, text="Starting analysis…")

        for i, path in enumerate(file_paths):
            filename = os.path.basename(path)
            progress.progress((i) / len(file_paths), text=f"Processing {filename}…")

            with st.spinner(f"Analysing {filename}…"):
                try:
                    text   = extract_text(path)
                    result = run_intellihire(text, job)

                    resume = result["resume"]
                    skills = result["skills"]
                    match  = result["match"]

                    name        = resume.get("name") or filename
                    score       = match.get("match_score", 0)
                    rec         = match.get("recommendation", "Maybe")
                    missing     = match.get("missing_skills", [])
                    matched     = match.get("matched_skills", [])
                    skills_list = skills.get("skills_list", [])

                    sc = score_class(score)
                    rc = rec_class(rec)

                    left, right = st.columns([3,1], gap="large")

                    with left:
                        st.markdown(f"""
                        <div class="result-card">
                            <h3 style="margin:0 0 0.3rem;color:#1e1b4b">{name}</h3>
                            <span style="color:#6b7280;font-size:0.86rem">
                                📧 {resume.get('email','—')} &nbsp;|&nbsp;
                                📞 {resume.get('phone','—')} &nbsp;|&nbsp;
                                💼 {resume.get('experience','—')} &nbsp;|&nbsp;
                                🎓 {resume.get('education','—')}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                        t1, t2, t3 = st.tabs(["📝 Summary", "🛠 Skills", "🎯 Job Match"])

                        with t1:
                            st.write(resume.get("ai_summary","—"))

                        with t2:
                            if skills_list:
                                st.markdown(
                                    " ".join(f'<span class="skill-pill">{s}</span>' for s in skills_list),
                                    unsafe_allow_html=True
                                )
                            else:
                                st.write(skills.get("skills_text","—"))

                        with t3:
                            st.write(match.get("match_summary","—"))
                            c1, c2 = st.columns(2)
                            with c1:
                                if matched:
                                    st.success("**✅ Matched:** " + ", ".join(matched))
                            with c2:
                                if missing:
                                    st.error("**❌ Missing:** " + ", ".join(missing))

                    with right:
                        st.markdown(f"""
                        <div class="score-badge {sc}">{score}%</div>
                        <div style="text-align:center">
                            <span class="rec-tag {rc}">{rec}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.plotly_chart(match_chart(score), use_container_width=True)

                    st.success(f"✅ {name} saved to database")

                except Exception as e:
                    st.error(f"❌ Error: {filename} — {str(e)}")
                    with st.expander("Error details"):
                        st.exception(e)

            st.markdown('<hr class="divider">', unsafe_allow_html=True)

        progress.progress(1.0, text="✅ All resumes processed!")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Dashboard
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":

    st.markdown('<div class="section-title">📊 Recruiter Dashboard</div>', unsafe_allow_html=True)

    candidates = get_candidates()

    if not candidates:
        st.info("No candidates yet. Go to **Analyze Resumes** to get started.")
    else:
        total  = len(candidates)
        hired  = sum(1 for c in candidates if c.recommendation in ("Strong Hire","Hire"))
        maybe  = sum(1 for c in candidates if c.recommendation == "Maybe")
        no_hire= sum(1 for c in candidates if c.recommendation == "No Hire")
        avg_sc = round(sum(c.match_score or 0 for c in candidates) / total)
        top    = max(candidates, key=lambda c: c.match_score or 0)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Candidates", total)
        m2.metric("✅ Hire / Strong Hire", hired)
        m3.metric("🤔 Maybe", maybe)
        m4.metric("❌ No Hire", no_hire)
        m5.metric("📈 Avg Score", f"{avg_sc}%")

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        col_chart, col_top = st.columns([2,1], gap="large")

        with col_chart:
            st.markdown("**Match Score Comparison**")
            st.plotly_chart(candidate_chart(candidates), use_container_width=True)

        with col_top:
            st.markdown("**🏆 Top Candidate**")
            sc = score_class(top.match_score or 0)
            rc = rec_class(top.recommendation or "")
            st.markdown(f"""
            <div class="result-card">
                <h4 style="margin:0 0 0.3rem;color:#1e1b4b">{top.name or '—'}</h4>
                <div class="score-badge {sc}" style="font-size:1.8rem;padding:0.6rem">{top.match_score or 0}%</div>
                <div style="text-align:center"><span class="rec-tag {rc}">{top.recommendation or '—'}</span></div>
                <p style="margin:0.6rem 0 0;font-size:0.82rem;color:#6b7280">{top.ai_summary[:120] + '…' if top.ai_summary and len(top.ai_summary)>120 else top.ai_summary or '—'}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # Filter bar
        st.markdown("**Filter candidates**")
        f1, f2, f3 = st.columns(3)
        with f1:
            filter_rec = st.multiselect(
                "Recommendation", ["Strong Hire","Hire","Maybe","No Hire"],
                default=["Strong Hire","Hire","Maybe","No Hire"]
            )
        with f2:
            min_score = st.slider("Min score", 0, 100, 0)
        with f3:
            sort_by = st.selectbox("Sort by", ["Score ↓","Score ↑","Name A-Z"])

        filtered = [
            c for c in candidates
            if (c.recommendation or "Maybe") in filter_rec
            and (c.match_score or 0) >= min_score
        ]

        if sort_by == "Score ↓":
            filtered.sort(key=lambda c: c.match_score or 0, reverse=True)
        elif sort_by == "Score ↑":
            filtered.sort(key=lambda c: c.match_score or 0)
        else:
            filtered.sort(key=lambda c: c.name or "")

        st.markdown(f"Showing **{len(filtered)}** of **{total}** candidates")

        for c in filtered:
            sc = score_class(c.match_score or 0)
            rc = rec_class(c.recommendation or "")
            with st.expander(f"**{c.name or 'Unknown'}**  —  {c.match_score or 0}%  |  {c.recommendation or '—'}"):
                left, right = st.columns([3,1])
                with left:
                    i1, i2 = st.columns(2)
                    with i1:
                        st.write(f"📧 **Email:** {c.email or '—'}")
                        st.write(f"💼 **Experience:** {c.experience or '—'}")
                    with i2:
                        st.write(f"📞 **Phone:** {c.phone or '—'}")
                        st.write(f"🎓 **Education:** {c.education or '—'}")
                    st.write(f"📝 **Summary:** {c.ai_summary or '—'}")
                    if c.skills:
                        st.markdown(skill_pills(c.skills), unsafe_allow_html=True)
                with right:
                    st.markdown(f"""
                    <div class="score-badge {sc}" style="font-size:1.8rem;padding:0.5rem">{c.match_score or 0}%</div>
                    <div style="text-align:center"><span class="rec-tag {rc}">{c.recommendation or '—'}</span></div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🗑 Delete", key=f"del_{c.candidate_id}"):
                        delete_candidate(c.candidate_id)
                        st.success(f"{c.name} deleted.")
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — All Candidates Table
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗂 All Candidates":

    st.markdown('<div class="section-title">🗂 All Candidates</div>', unsafe_allow_html=True)

    candidates = get_candidates()

    if not candidates:
        st.info("No candidates yet.")
    else:
        # Quick delete bar for old/broken records
        st.markdown("Select candidates to delete:")

        for c in sorted(candidates, key=lambda x: x.match_score or 0, reverse=True):
            sc = score_class(c.match_score or 0)
            rc = rec_class(c.recommendation or "")

            col_name, col_score, col_rec, col_del = st.columns([3, 1, 1.5, 1])
            with col_name:
                st.write(f"**{c.name or 'Unknown'}**")
                st.caption(f"{c.email or '—'}  |  {c.experience or '—'}")
            with col_score:
                st.markdown(
                    f'<span class="rec-tag {sc}" style="font-size:0.9rem">{c.match_score or 0}%</span>',
                    unsafe_allow_html=True
                )
            with col_rec:
                st.markdown(
                    f'<span class="rec-tag {rc}">{c.recommendation or "—"}</span>',
                    unsafe_allow_html=True
                )
            with col_del:
                if st.button("🗑", key=f"tbl_del_{c.candidate_id}", help=f"Delete {c.name}"):
                    delete_candidate(c.candidate_id)
                    st.success(f"Deleted {c.name}")
                    st.rerun()

            st.markdown('<hr class="divider">', unsafe_allow_html=True)