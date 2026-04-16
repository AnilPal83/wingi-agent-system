from core.orchestrator import Orchestrator
from core.logger import setup_logger
import os

logger = setup_logger("Main")

def main():
    # Load Goal
    logger.info("System Starting...")
    goal = input("🎯 What would you like to build today? ") or "A simple portfolio website"
    
    print("\n--- AGENT SYSTEM STARTING ---")
    orchestrator = Orchestrator(project_name="MyGeneratedApp", user_goal=goal)
    
    # 1. Generate the Plan
    logger.info("Planning Stage starting...")
    orchestrator.bootstrap_plan()
    
    # 2. Execute the Loop
    logger.info("Execution Stage starting...")
    cycle_count = 0
    while orchestrator.is_running:
        cycle_count += 1
        logger.info(f"--- [ STARTING ENGINE CYCLE {cycle_count} ] ---")
        orchestrator.run_cycle()

    logger.info("Project completed. System shutting down.")

if __name__ == "__main__":
    main()