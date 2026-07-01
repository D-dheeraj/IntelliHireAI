"""
IntelliHire MCP Server — Live Demo Script
==========================================
Run this to see all 6 MCP tools in action.
Perfect for video recording / Kaggle submission demo.

Usage:
    source .venv/bin/activate
    python demo_mcp.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Load our FastMCP server ────────────────────────────────────────────────────
import importlib.util
spec = importlib.util.spec_from_file_location(
    "intellihire_mcp_server",
    os.path.join(os.path.dirname(__file__), "mcp", "server.py"),
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# ── Pretty print helpers ───────────────────────────────────────────────────────
W  = "\033[0m"     # reset
B  = "\033[1m"     # bold
CY = "\033[96m"    # cyan
GR = "\033[92m"    # green
YL = "\033[93m"    # yellow
MG = "\033[95m"    # magenta
RD = "\033[91m"    # red

def header(text):
    print(f"\n{CY}{'─'*60}{W}")
    print(f"{B}{CY}  {text}{W}")
    print(f"{CY}{'─'*60}{W}")

def tool_call(name, result):
    print(f"\n  {MG}🔧 Tool Called:{W} {B}{name}{W}")
    print(f"  {GR}✅ Result:{W}")
    print(f"  {json.dumps(result, indent=4, default=str)}")

def section(text):
    print(f"\n  {YL}▶  {text}{W}")

# ══════════════════════════════════════════════════════════════════════════════
header("IntelliHire AI — MCP Server Demo")
# ══════════════════════════════════════════════════════════════════════════════

# ── Show all registered MCP tools ─────────────────────────────────────────────
header("📋 Registered MCP Tools (FastMCP)")
tools = mod.mcp._tool_manager.list_tools()
print(f"\n  {B}Server:{W} {mod.mcp.name}")
print(f"  {B}Tools exposed:{W} {len(tools)}\n")
for i, t in enumerate(tools, 1):
    desc_first_line = (t.description or "").strip().split("\n")[0][:65]
    print(f"  {GR}{i}.{W} {B}{t.name:<35}{W} {desc_first_line}")

# ══════════════════════════════════════════════════════════════════════════════
header("🚀 Simulating Full Hiring Pipeline via MCP Tools")
# ══════════════════════════════════════════════════════════════════════════════

# TOOL 1 — Log pipeline start
section("Manager Agent starts workflow → MCP: log_agent_action")
r1 = mod.log_agent_action(
    agent_name="Manager Agent",
    action="Workflow started — processing resume",
)
tool_call("log_agent_action", r1)

# TOOL 2 — Log Resume Agent
section("Resume Agent finishes → MCP: log_agent_action")
r2 = mod.log_agent_action(
    agent_name="Resume Agent",
    action="Resume analyzed",
    output_data='{"name": "Priya Sharma", "email": "priya@example.com", "experience": "4 years"}',
)
tool_call("log_agent_action", r2)

# TOOL 3 — Log Skill Agent
section("Skill Agent finishes → MCP: log_agent_action")
r3 = mod.log_agent_action(
    agent_name="Skill Agent",
    action="Skills extracted",
    output_data="Python, FastAPI, React, PostgreSQL, Docker, AWS",
)
tool_call("log_agent_action", r3)

# TOOL 4 — Log Matching Agent
section("Matching Agent finishes → MCP: log_agent_action")
r4 = mod.log_agent_action(
    agent_name="Matching Agent",
    action="Match complete — score=87, rec=Strong Hire",
    output_data='{"match_score": 87, "recommendation": "Strong Hire"}',
)
tool_call("log_agent_action", r4)

# TOOL 5 — Save candidate via MCP
section("Manager Agent saves candidate → MCP: save_candidate_record")
r5 = mod.save_candidate_record(
    name="Priya Sharma",
    email="priya@example.com",
    phone="+91-9876543210",
    experience="4 years",
    education="B.Tech Computer Science, IIT Delhi",
    skills="Python, FastAPI, React, PostgreSQL, Docker, AWS",
    match_score=87,
    ai_summary=(
        "Senior full-stack engineer with 4 years experience in Python and React. "
        "Strong background in cloud infrastructure and API design."
    ),
    recommendation="Strong Hire",
    resume_text="[Resume text truncated for demo]",
)
tool_call("save_candidate_record", r5)

candidate_id = r5.get("candidate_id")

# TOOL 6 — Link logs to candidate
section(f"Linking audit logs to candidate #{candidate_id} → MCP: link_logs_to_candidate")
r6 = mod.link_logs_to_candidate(candidate_id=candidate_id, limit=10)
tool_call("link_logs_to_candidate", r6)

# ══════════════════════════════════════════════════════════════════════════════
header("📊 Query Tools")
# ══════════════════════════════════════════════════════════════════════════════

# TOOL 7 — Get all candidates
section("Dashboard query → MCP: get_all_candidates")
r7 = mod.get_all_candidates()
tool_call("get_all_candidates", {
    "total_candidates": len(r7["candidates"]),
    "latest": r7["candidates"][:2],   # show max 2 for brevity
})

# TOOL 8 — Get audit trail
section(f"Audit trail for candidate #{candidate_id} → MCP: get_candidate_audit_trail")
r8 = mod.get_candidate_audit_trail(candidate_id=candidate_id)
tool_call("get_candidate_audit_trail", {
    "log_count": len(r8["logs"]),
    "logs": r8["logs"],
})

# ══════════════════════════════════════════════════════════════════════════════
header("✅ Demo Complete")
# ══════════════════════════════════════════════════════════════════════════════
print(f"""
  {GR}{B}All 6 MCP tools demonstrated successfully!{W}

  {B}Summary:{W}
  • FastMCP server: {mod.mcp.name}
  • Tools exposed : {len(tools)}
  • Protocol      : Model Context Protocol (MCP)
  • Transport     : In-process (cloud-safe) + stdio (mcp run mcp/server.py)
  • Database      : SQLite via SQLAlchemy ORM
  • Agents wired  : Manager → Resume → Skill → Matching → MCP Server → DB

  {YL}Run the full app:{W}  streamlit run app/streamlit_app.py
  {YL}Standalone server:{W} mcp run mcp/server.py
""")
