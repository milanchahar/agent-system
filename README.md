# 3-Agent AI Incident Response System

> An autonomous multi-agent pipeline that ingests production logs, diagnoses root causes, researches fixes from live documentation, and produces a step-by-step operator runbook — all without human intervention.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Agent Responsibilities](#agent-responsibilities)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the System](#running-the-system)
- [Sample Output](#sample-output)
- [Agent Handoff Design](#agent-handoff-design)
- [Design Decisions](#design-decisions)


---

## Overview

This project implements a **3-Agent AI Incident Response System** for Linux-hosted production APIs. When an incident occurs — spiking latency, login failures, portfolio endpoint errors — the system automatically:

1. Reads and analyzes the raw log files
2. Researches fixes from live technical documentation
3. Produces a safe, ordered remediation runbook with rollback instructions

**Incident scenario simulated:**
- API latency increased sharply over 20 minutes
- Users reporting failures on `/api/login` and `/api/portfolio`
- Load balancer health check intermittently passing

---

## System Architecture

```
┌─────────────────┐
│   Log Files     │  nginx-access.log
│   (Input)       │  nginx-error.log
│                 │  app-error.log
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  Agent 1 — Log Analysis Agent          [Gemini LLM]    │
│  Reads logs → identifies root cause → structured JSON  │
└────────────────────────┬────────────────────────────────┘
                         │  JSON handoff
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Agent 2 — Solution Research Agent     [Web Scraping]  │
│  Fetches live docs → compares solutions → ranks fixes  │
└────────────────────────┬────────────────────────────────┘
                         │  JSON handoff
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Agent 3 — Resolution Planner Agent    [Gemini LLM]    │
│  Selects safest fix → writes runbook → adds rollback   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
              Final Incident Report
         (terminal output + 3 JSON files)
```

---

## Agent Responsibilities

### 🔍 Agent 1 — Log Analysis Agent

**Model:** Gemini 2.5 Flash  
**Input:** `nginx-access.log`, `nginx-error.log`, `app-error.log`

Responsibilities:
- Read and parse all three log files
- Identify the most likely root cause with evidence
- Assign a confidence level (HIGH / MEDIUM / LOW)
- Extract supporting log snippets
- Surface alternate hypotheses and open questions
- Output structured JSON for Agent 2

**Output fields:** `root_cause`, `evidence[]`, `confidence`, `confidence_reason`, `alternate_hypotheses[]`, `open_questions[]`, `diagnosis_keywords[]`, `recommended_research_topics[]`

---

### Agent 2 — Solution Research Agent

**Model:** None (web scraping only — no LLM)  
**Input:** Agent 1 JSON output

Responsibilities:
- Use `diagnosis_keywords` from Agent 1 to guide research
- Scrape live technical documentation (PostgreSQL, nginx, PgBouncer)
- Define multiple solution options with pros, cons, and risk levels
- Flag HIGH-risk actions that should not be tried first in production
- Output structured solution list for Agent 3

**Sources scraped:**
- https://www.postgresql.org/docs/current/runtime-config-connection.html
- https://nginx.org/en/docs/http/ngx_http_upstream_module.html
- https://www.pgbouncer.org/config.html

**Output fields:** `research_context{}`, `solutions[]`, `risky_actions_flagged[]`, `recommended_first_actions[]`

---

### Agent 3 — Resolution Planner Agent

**Model:** Gemini 2.5 Flash  
**Input:** Agent 1 JSON + Agent 2 JSON

Responsibilities:
- Review all evidence and solution options
- Select the safest, most practical first action
- Write ordered step-by-step remediation instructions
- Include pre-checks, validation steps, and rollback plan
- Flag whether downtime is required
- Define escalation triggers

**Output fields:** `selected_solution`, `selection_rationale`, `pre_checks[]`, `remediation_steps[]`, `validation_checks[]`, `rollback_plan`, `downtime_required`, `escalation_triggers[]`, `post_incident_tasks[]`

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| LLM (Agent 1 & 3) | Gemini 2.5 Flash (`google-generativeai`) |
| Web Scraping (Agent 2) | `requests` + `BeautifulSoup4` |
| Agent Communication | Structured JSON files |
| Config Management | `python-dotenv` |
| Environment | Linux / macOS / WSL |

---

## Project Structure

```
incident-agent-system/
├── agents/
│   ├── agent1_log_analysis.py      # Gemini-powered log analysis
│   ├── agent2_solution_research.py # Web scraping, no LLM
│   └── agent3_resolution_planner.py # Gemini-powered runbook generation
│
├── logs/
│   ├── nginx-access.log            # Sample access log with 504/502 errors
│   ├── nginx-error.log             # Upstream timeout errors
│   └── app-error.log               # DB connection pool exhaustion
│
├── output_agent1.json              # Agent 1 diagnosis (generated at runtime)
├── output_agent2.json              # Agent 2 solutions  (generated at runtime)
├── output_agent3.json              # Agent 3 runbook    (generated at runtime)
│
├── main.py                         # Orchestrator — runs all 3 agents in sequence
├── requirements.txt                # Python dependencies
├── .env                            # API key (never commit this)
├── .gitignore                      # Excludes .env, venv, __pycache__, outputs
└── README.md
```

---

## Prerequisites

- Python 3.10 or higher
- pip
- Internet access (for Agent 2 web scraping)
- A Gemini API key

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/milanchahar/agent-system.git
cd incident-agent-system

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

**requirements.txt:**
```
google-generativeai>=0.5.0
requests>=2.31.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
```


## Running the System

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the full 3-agent pipeline
python main.py
```

The system runs in three phases and takes approximately 30–60 seconds end-to-end.

**Expected terminal output:**
```
============================================================
INCIDENT RESPONSE SYSTEM — STARTING
============================================================

[PHASE 1] Log Analysis Agent
[Agent 1] Reading logs...
[Agent 1] Sending to Gemini for analysis...
[Agent 1] Root cause identified: Database connection pool exhaustion...
[Agent 1] Confidence: HIGH
  Saved: output_agent1.json

[PHASE 2] Solution Research Agent
[Agent 2] Starting solution research (web scraping)...
[Agent 2] Fetching: https://www.postgresql.org/docs/...
[Agent 2] Found 4 solutions. Flagged risky: ['Restart the application service']
  Saved: output_agent2.json

[PHASE 3] Resolution Planner Agent
[Agent 3] Building resolution plan with Gemini...
[Agent 3] Selected solution: Kill long-running/idle DB connections
  Saved: output_agent3.json

============================================================
FINAL INCIDENT REPORT
============================================================

ROOT CAUSE:     Database connection pool exhaustion due to slow queries
CONFIDENCE:     HIGH
BEST FIX:       Kill long-running/idle DB connections
DOWNTIME?:      NO

REMEDIATION STEPS:
  Step 1: Connect to PostgreSQL: psql -U postgres -h localhost
  Step 2: Check active connections: SELECT count(*) FROM pg_stat_activity;
  Step 3: Identify idle connections older than 5 minutes
  Step 4: Terminate idle connections with pg_terminate_backend()
  Step 5: Monitor connection count drop in real-time

ROLLBACK:       Stop termination query. If pool remains exhausted,
                increase pool_size in app config and reload.

All outputs saved to output_agent*.json
```

---

## Sample Output

### Agent 1 Output (`output_agent1.json`)

```json
{
  "root_cause": "Database connection pool exhaustion caused by slow queries blocking all available connections",
  "confidence": "HIGH",
  "confidence_reason": "Multiple log files converge on the same symptom: pool full, queries timing out, upstream failures cascading to 504s",
  "evidence": [
    {
      "log_file": "app-error.log",
      "snippet": "All connections exhausted. Pool size: 10/10. Queue: 47 waiting.",
      "significance": "Direct confirmation that the connection pool is fully occupied"
    },
    {
      "log_file": "nginx-error.log",
      "snippet": "upstream timed out (110: Connection timed out) while reading response header",
      "significance": "Nginx cannot get responses because the app is blocked waiting for DB"
    }
  ],
  "alternate_hypotheses": [
    {
      "hypothesis": "Memory leak causing OOM kills",
      "reasoning": "No OOM killer messages observed in provided logs"
    }
  ],
  "diagnosis_keywords": ["connection pool", "timeout", "postgresql", "pg_stat_activity"]
}
```

### Agent 3 Output (`output_agent3.json`) — abbreviated

```json
{
  "selected_solution": "Kill long-running/idle DB connections",
  "downtime_required": false,
  "pre_checks": [
    "Confirm you have psql access with superuser or pg_signal_backend privilege",
    "Check current connection count: SELECT count(*) FROM pg_stat_activity;"
  ],
  "remediation_steps": [
    {
      "step": 1,
      "action": "psql -U postgres -h localhost",
      "purpose": "Connect to the database",
      "expected_output": "psql prompt appears"
    },
    {
      "step": 2,
      "action": "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < NOW() - INTERVAL '5 minutes';",
      "purpose": "Free stale connections without restarting the service",
      "expected_output": "One row returned per terminated connection, value: t"
    }
  ],
  "rollback_plan": "If terminating connections causes further errors, stop the query immediately. Increase pool_size in application config and reload without restart."
}
```

---

## Agent Handoff Design

Agents pass structured JSON between phases. This makes the pipeline:
- **Debuggable** — inspect any `output_agent*.json` file to see exactly what each agent produced
- **Modular** — swap out any agent independently without changing the others
- **Testable** — run agents individually with mock inputs

```
Agent 1 → Agent 2
{
  "root_cause": "...",
  "confidence": "HIGH",
  "evidence": [...],
  "diagnosis_keywords": ["connection pool", "timeout"]
}

Agent 2 → Agent 3
{
  "solutions": [
    {"title": "...", "risk": "LOW", "try_first": true, "pros": [...], "cons": [...]}
  ],
  "risky_actions_flagged": ["Restart the application service"]
}
```

---

## Design Decisions

### Clear Agent Separation
Each agent has exactly one responsibility. Agent 1 only analyzes. Agent 2 only researches. Agent 3 only plans. This prevents a single agent from becoming a bottleneck and makes each step independently testable.

### No LLM in Agent 2
The brief explicitly forbids using an LLM as the primary research mechanism in Agent 2. Web scraping against official documentation (PostgreSQL, nginx, PgBouncer docs) gives source-backed, verifiable recommendations rather than hallucinated suggestions.

### Safety-First Solution Ranking
High-risk actions (like restarting the application service) are explicitly flagged by Agent 2 and passed to Agent 3's prompt as actions to avoid attempting first. The Gemini prompt for Agent 3 reinforces this constraint.

### JSON as Handoff Format
Pure JSON ensures each agent's output is machine-readable, human-inspectable, and forward-compatible. No parsing of free-text between agents.

### Prompts Visible in Source
Both Gemini prompts (`ANALYSIS_PROMPT` and `PLANNING_PROMPT`) are defined as string constants at the top of their respective files — fully visible and auditable without running the code.

# Thank you.