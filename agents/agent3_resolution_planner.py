import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

PLANNING_PROMPT = """
You are a principal engineer writing a production incident runbook for an on-call operator.
You have received a diagnosis from Agent 1 and a list of vetted solutions from Agent 2.

=== Agent 1 Diagnosis ===
Root cause: {root_cause}
Confidence: {confidence}
Evidence snippets:
{evidence}

=== Agent 2 Solutions ===
{solutions}

Risky actions flagged (do NOT start with these): {risky_actions}
Recommended first actions: {first_actions}

Your task:
1. Select the single safest and most practical solution to attempt FIRST in production.
2. Write an ordered step-by-step remediation plan an operator can follow without prior context.
3. Include pre-checks (things to verify BEFORE starting).
4. Include validation steps (how to confirm the fix is working DURING and AFTER).
5. Include a rollback plan if the fix makes things worse.
6. Flag anything that requires a maintenance window or causes downtime.

Respond ONLY in the following JSON format, no markdown, no preamble:
{{
  "selected_solution": "<solution title>",
  "selection_rationale": "<why this solution is safest and most effective first>",
  "pre_checks": [
    "<check 1>",
    "<check 2>"
  ],
  "remediation_steps": [
    {{"step": 1, "action": "<exact command or action>", "purpose": "<why>", "expected_output": "<what success looks like>"}},
    {{"step": 2, "action": "<...>", "purpose": "<...>", "expected_output": "<...>"}}
  ],
  "validation_checks": [
    "<validation step 1>",
    "<validation step 2>"
  ],
  "rollback_plan": "<what to do if this fix causes more problems>",
  "downtime_required": false,
  "escalation_triggers": ["<when to escalate to senior engineer>"],
  "post_incident_tasks": ["<follow-up action 1>", "<follow-up action 2>"]
}}
"""

def run(agent1_output: dict, agent2_output: dict) -> dict:
    print("[Agent 3] Building resolution plan with Gemini...")

    evidence_str = "\n".join(
        f"- [{e['log_file']}] {e['snippet']} ({e['significance']})"
        for e in agent1_output.get("evidence", [])
    )

    solutions_str = "\n".join(
        f"Solution {i+1}: {s['title']}\n  Risk: {s['risk']}\n  Description: {s['description']}\n  Pros: {', '.join(s['pros'])}\n  Cons: {', '.join(s['cons'])}"
        for i, s in enumerate(agent2_output["solutions"])
    )

    prompt = PLANNING_PROMPT.format(
        root_cause=agent1_output["root_cause"],
        confidence=agent1_output["confidence"],
        evidence=evidence_str,
        solutions=solutions_str,
        risky_actions=", ".join(agent2_output["risky_actions_flagged"]),
        first_actions=", ".join(agent2_output["recommended_first_actions"])
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    print(f"[Agent 3] Selected solution: {result['selected_solution']}")
    return result