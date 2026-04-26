# Incident Response Agent System

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install google-genai requests beautifulsoup4 python-dotenv
# Add your GEMINI_API_KEY to the .env file
```

## Run
```bash
python main.py
```

## Output
- `output_agent1.json` — log analysis + root cause
- `output_agent2.json` — solution options with web sources
- `output_agent3.json` — final runbook with steps
