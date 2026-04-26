import json
from agents.agent1_log_analysis import run as run_agent1
from agents.agent2_solution_research import run as run_agent2
from agents.agent3_resolution_planner import run as run_agent3

def save_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved: {filename}")

def main():
    print("=" * 60)
    print("INCIDENT RESPONSE SYSTEM — STARTING")
    print("=" * 60)

    # Agent 1
    print("\n[PHASE 1] Log Analysis Agent")
    agent1_result = run_agent1()
    save_json(agent1_result, "output_agent1.json")

    # Agent 2
    print("\n[PHASE 2] Solution Research Agent")
    agent2_result = run_agent2(agent1_result)
    save_json(agent2_result, "output_agent2.json")

    # Agent 3
    print("\n[PHASE 3] Resolution Planner Agent")
    agent3_result = run_agent3(agent1_result, agent2_result)
    save_json(agent3_result, "output_agent3.json")

    # Final Report
    print("\n" + "=" * 60)
    print("FINAL INCIDENT REPORT")
    print("=" * 60)
    print(f"\nROOT CAUSE:     {agent1_result['root_cause']}")
    print(f"CONFIDENCE:     {agent1_result['confidence']}")
    print(f"BEST FIX:       {agent3_result['selected_solution']}")
    print(f"DOWNTIME?:      {'YES' if agent3_result['downtime_required'] else 'NO'}")
    print(f"\nREMEDIATION STEPS:")
    for step in agent3_result['remediation_steps']:
        print(f"  Step {step['step']}: {step['action']}")
    print(f"\nROLLBACK:       {agent3_result['rollback_plan']}")
    print("\nAll outputs saved to output_agent*.json")

if __name__ == "__main__":
    main()