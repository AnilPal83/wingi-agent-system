from core.orchestrator import Orchestrator
import os

def main():
    # Load Goal
    goal = input("🎯 What would you like to build today? ") or "A simple portfolio website"
    
    print("\n--- AGENT SYSTEM STARTING ---")
    orchestrator = Orchestrator(project_name="MyGeneratedApp", user_goal=goal)
    
    # 1. Generate the Plan
    orchestrator.bootstrap_plan()
    
    # 2. Execute the Loop
    while orchestrator.is_running:
        orchestrator.run_cycle()

if __name__ == "__main__":
    main()