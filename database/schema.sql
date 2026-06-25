-- Candidates table
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id  SERIAL PRIMARY KEY,
    name          VARCHAR(100),
    email         VARCHAR(100),
    phone         VARCHAR(20),
    experience    VARCHAR(100),
    education     VARCHAR(200),
    resume_text   TEXT,
    skills        TEXT,
    match_score   INTEGER,
    ai_summary    TEXT,
    recommendation TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Skills table
CREATE TABLE IF NOT EXISTS skills (
    skill_id     SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    skill_name   VARCHAR(100)
);


-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id             SERIAL PRIMARY KEY,
    job_title          VARCHAR(100),
    required_skills    TEXT,
    experience_required INTEGER
);


-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    application_id SERIAL PRIMARY KEY,
    candidate_id   INTEGER REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    job_id         INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
    match_score    FLOAT,
    status         VARCHAR(50)
);


-- Agent Logs table
CREATE TABLE IF NOT EXISTS agent_logs (
    id           SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(candidate_id) ON DELETE SET NULL,
    agent_name   VARCHAR(100),
    action       VARCHAR(200),
    input_data   TEXT,
    output_data  TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
