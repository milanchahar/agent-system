import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def read_logs():
    logs = {}
    for fname in ["nginx-access.log", "nginx-error.log", "app-error.log"]:
        path = os.path.join("logs", fname)
        with open(path, "r") as f:
            logs[fname] = f.read()
    return logs

ANALYSIS_PROMPT = """
You are a senior site-reliability engineer performing incident triage.
You have been given three log files from a Linux production API that is experiencing:
- Sharp increase in API latency over the last 20 minutes
- User-reported failures on /api/login and /api/portfolio endpoints
- Intermittent health check failures from the load balancer

=== nginx-access.log ===
{nginx_access}

=== nginx-error.log ===
{nginx_error}

=== app-error.log ===
{app_error}

Your task:
1. Identify the most likely root cause of this incident.
2. Extract the 3-5 strongest log snippets that directly support your conclusion.
3. Assign a confidence level: HIGH / MEDIUM / LOW and explain why.
4. List any alternate hypotheses with brief reasoning.
5. List specific diagnostic questions still unanswered from these logs alone.

Respond ONLY in the following JSON format, no markdown, no preamble:
{{
  "root_cause": "<one-sentence description>",
  "evidence": [
    {{"log_file": "<filename>", "snippet": "<exact log line or pattern>", "significance": "<why this matters>"}}
  ],
  "confidence": "HIGH|MEDIUM|LOW",
  "confidence_reason": "<why you chose this confidence level>",
  "alternate_hypotheses": [
    {{"hypothesis": "<alternate cause>", "reasoning": "<why it's less likely>"}}
  ],
  "open_questions": ["<question 1>", "<question 2>"],
  "diagnosis_keywords": ["<keyword for Agent 2 to search>"],
  "recommended_research_topics": ["<topic 1>", "<topic 2>"]
}}
"""

def run():
    print("[Agent 1] Reading logs...")
    logs = read_logs()

    prompt = ANALYSIS_PROMPT.format(
        nginx_access=logs["nginx-access.log"],
        nginx_error=logs["nginx-error.log"],
        app_error=logs["app-error.log"]
    )

    print("[Agent 1] Sending to Gemini for analysis...")
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    
    raw = response.text.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    print(f"[Agent 1] Root cause identified: {result['root_cause']}")
    print(f"[Agent 1] Confidence: {result['confidence']}")
    return result

if __name__ == "__main__":
    import pprint
    pprint.pprint(run())