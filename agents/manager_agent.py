from agents.resume_agent import analyze_resume
from agents.skill_agent import extract_skills
from agents.matching_agent import match_candidate

from mcp.server import IntelliHireMCP


mcp = IntelliHireMCP()


def run_intellihire(resume_text, job_description):
    """
    Takes raw resume text and a job description, runs it through all three agents,
    saves everything to the database, and returns the results.
    """

    mcp.log(agent="Manager Agent", action="Workflow started")

    # first pass - get the basic candidate info
    mcp.log(agent="Resume Agent", action="Analyzing resume")
    resume_data = analyze_resume(resume_text)
    mcp.log(
        agent="Resume Agent",
        action="Resume analyzed",
        output_data=str(resume_data)
    )

    # now pull out all the skills from the same resume
    mcp.log(agent="Skill Agent", action="Extracting skills")
    skill_data = extract_skills(resume_text)
    mcp.log(
        agent="Skill Agent",
        action="Skills extracted",
        output_data=skill_data.get("skills_text", "")
    )

    # compare skills against job requirements and get a score
    mcp.log(agent="Matching Agent", action="Matching against job")
    match_data = match_candidate(
        skill_data.get("skills_text", ""),
        job_description
    )
    mcp.log(
        agent="Matching Agent",
        action="Match complete",
        output_data=str(match_data)
    )

    # put everything together into one dict before saving
    candidate_record = {
        "name":           resume_data.get("name"),
        "email":          resume_data.get("email"),
        "phone":          resume_data.get("phone"),
        "experience":     resume_data.get("experience"),
        "education":      resume_data.get("education"),
        "resume_text":    resume_text,
        "skills":         skill_data.get("skills_text", ""),
        "match_score":    match_data.get("match_score", 0),
        "ai_summary":     resume_data.get("ai_summary", ""),
        "recommendation": match_data.get("recommendation", ""),
    }

    # save to database
    candidate = mcp.save_candidate_data(candidate_record)

    # link the logs we just created to this candidate
    if candidate:
        mcp.update_logs_candidate(candidate.candidate_id)

    mcp.log(
        agent="Manager Agent",
        action="Workflow complete",
        candidate_id=candidate.candidate_id if candidate else None
    )

    return {
        "candidate":   candidate,
        "resume":      resume_data,
        "skills":      skill_data,
        "match":       match_data,
    }
