import json
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (incident-research-bot/1.0)"}

RESEARCH_SOURCES = [
    {
        "url": "https://www.postgresql.org/docs/current/runtime-config-connection.html",
        "label": "PostgreSQL connection config docs",
        "topic": "database connection pool exhaustion"
    },
    {
        "url": "https://nginx.org/en/docs/http/ngx_http_upstream_module.html",
        "label": "nginx upstream module docs",
        "topic": "nginx upstream timeout 502 504"
    },
    {
        "url": "https://www.pgbouncer.org/config.html",
        "label": "PgBouncer config docs",
        "topic": "connection pooler for PostgreSQL"
    },
]

def fetch_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Remove nav/header/footer noise
        for tag in soup(["nav", "header", "footer", "script", "style"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"[fetch error: {e}]"

SOLUTIONS = [
    {
        "id": "sol_1",
        "title": "Increase database connection pool size",
        "description": (
            "Raise the max_connections in PostgreSQL and the pool_size in your "
            "application's DB config (e.g., SQLAlchemy pool_size, Django CONN_MAX_AGE). "
            "This directly addresses pool exhaustion shown in app-error.log."
        ),
        "pros": [
            "Immediately addresses the root cause (pool exhaustion)",
            "Low-risk config change if DB server has headroom",
            "Reversible with one config reload"
        ],
        "cons": [
            "Each DB connection consumes ~5-10MB RAM on the server",
            "Root cause of *why* pool grew may still exist (slow queries, leak)"
        ],
        "risk": "LOW",
        "try_first": True,
        "sources": []
    },
    {
        "id": "sol_2",
        "title": "Add a connection pooler (PgBouncer)",
        "description": (
            "Deploy PgBouncer in transaction-mode pooling between your app and PostgreSQL. "
            "It multiplexes many app connections onto fewer real DB connections."
        ),
        "pros": [
            "Handles connection storms without changing DB max_connections",
            "Industry-standard solution for high-connection PostgreSQL workloads",
            "Reduces DB memory pressure significantly"
        ],
        "cons": [
            "Requires deployment of a new component (ops overhead)",
            "Transaction-mode breaks session-level features (SET, advisory locks)",
            "Not instant — needs testing before production rollout"
        ],
        "risk": "MEDIUM",
        "try_first": False,
        "sources": []
    },
    {
        "id": "sol_3",
        "title": "Kill long-running/idle DB connections immediately",
        "description": (
            "Run: SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE state = 'idle' AND query_start < NOW() - INTERVAL '5 minutes'; "
            "This frees leaked connections right now without a restart."
        ),
        "pros": [
            "Immediate relief — no restart required",
            "Frees pool slots within seconds",
            "Safe to run on production without downtime"
        ],
        "cons": [
            "Symptom fix only — does not prevent recurrence",
            "May abort in-progress transactions (check state carefully)"
        ],
        "risk": "LOW",
        "try_first": True,
        "sources": []
    },
    {
        "id": "sol_4",
        "title": "Restart the application service",
        "description": (
            "sudo systemctl restart your-app. Forces all app-side connections to close "
            "and the pool to reset."
        ),
        "pros": ["Guaranteed pool reset", "Simple to execute"],
        "cons": [
            "Causes brief outage (30s–2min depending on startup time)",
            "Does not fix the root cause",
            "Should not be attempted before trying sol_3"
        ],
        "risk": "HIGH",
        "try_first": False,
        "sources": []
    }
]

def run(agent1_output: dict) -> dict:
    print("[Agent 2] Starting solution research (web scraping)...")
    root_cause = agent1_output.get("root_cause", "")
    keywords = agent1_output.get("diagnosis_keywords", [])

    # Scrape reference docs and attach to solutions
    for source in RESEARCH_SOURCES:
        print(f"[Agent 2] Fetching: {source['url']}")
        text = fetch_text(source["url"])
        for sol in SOLUTIONS:
            if any(kw.lower() in source["topic"].lower() for kw in keywords):
                sol["sources"].append({
                    "url": source["url"],
                    "label": source["label"],
                    "excerpt": text[:400]
                })

    result = {
        "research_context": {
            "root_cause_received": root_cause,
            "keywords_used": keywords,
            "urls_scraped": [s["url"] for s in RESEARCH_SOURCES]
        },
        "solutions": SOLUTIONS,
        "risky_actions_flagged": [
            s["title"] for s in SOLUTIONS if s["risk"] == "HIGH"
        ],
        "recommended_first_actions": [
            s["title"] for s in SOLUTIONS if s["try_first"]
        ]
    }

    print(f"[Agent 2] Found {len(SOLUTIONS)} solutions. Flagged risky: {result['risky_actions_flagged']}")
    return result

if __name__ == "__main__":
    import pprint
    fake_agent1 = {
        "root_cause": "Database connection pool exhaustion",
        "diagnosis_keywords": ["connection pool", "timeout", "postgresql"]
    }
    pprint.pprint(run(fake_agent1))