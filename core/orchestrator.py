from .models import TaskGraph, TaskNode, TaskStatus, TaskType
from .llm_client import LLMClient
from .logger import setup_logger
from tools.registry import ToolBox
from agents.prompts import ORCHESTRATOR_SYSTEM_PROMPT, CODER_SYSTEM_PROMPT, MEMORY_AGENT_SYSTEM_PROMPT
import json
import os

logger = setup_logger("Orchestrator")

class Orchestrator:
    def __init__(self, project_name: str, user_goal: str):
        self.graph = TaskGraph(project_name=project_name)
        self.user_goal = user_goal
        self.llm = LLMClient()
        self.toolbox = ToolBox()
        self.is_running = True
        self.workspace = f"/root/workspace/{project_name}"
        logger.info(f"Initialized Orchestrator for project '{project_name}'. Workspace: {self.workspace}")

    def bootstrap_plan(self):
        """Asks the Planner LLM to generate the initial graph."""
        logger.info(f"Planning the project based on goal: '{self.user_goal}'")
        prompt = f"Goal: {self.user_goal}\n\nDecompose this into a valid JSON TaskGraph. Include a 'memory' task after architectural design to map the project. Output only the 'nodes' array."
        plan = self.llm.query(ORCHESTRATOR_SYSTEM_PROMPT, prompt, response_format="json")
        
        if plan and "nodes" in plan:
            for node_data in plan["nodes"]:
                node = TaskNode(**node_data)
                self.graph.nodes[node.id] = node
            logger.info(f"Created Task Graph with {len(self.graph.nodes)} nodes.")
            logger.debug(f"Nodes: {[n.id for n in self.graph.nodes.values()]}")
        else:
            logger.error("Failed to bootstrap the initial plan.")
            self.is_running = False

    def run_cycle(self):
        """The core loop: Find tasks -> Execute -> Handle Results."""
        logger.info("Cycle start. Checking for runnable tasks...")
        runnable = self.graph.get_runnable_tasks()
        
        if not runnable:
            if all(n.status == TaskStatus.COMPLETED for n in self.graph.nodes.values()):
                logger.info("All tasks in graph are COMPLETED.")
                self.is_running = False
                print("\n🏁 Project Complete.")
            else:
                logger.warning("No runnable tasks found, but some tasks are still pending/failed.")
            return

        for task in runnable:
            self.execute_task(task)

    def execute_task(self, task: TaskNode):
        task.status = TaskStatus.RUNNING
        logger.info(f"Executing [ {task.type.value.upper()} ] Task {task.id}: '{task.description}'...")

        if task.type == TaskType.CODE:
            # Get implementation from Coder Agent
            logger.debug(f"Requesting implementation for Task {task.id} from Coder Agent...")
            coder_prompt = f"Task: {task.description}\nContext: {task.input_context}\nWrite the code and return it as JSON: {{'filename': '...', 'content': '...'}}"
            result = self.llm.query(CODER_SYSTEM_PROMPT, coder_prompt, response_format="json")
            
            if result:
                path = f"{self.workspace}/{result['filename']}"
                status = self.toolbox.write_file(path, result['content'])
                task.status = TaskStatus.COMPLETED
                task.output = status
                logger.info(f"Coder Agent successfully generated {result['filename']}. Status: {status}")
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Coder Agent failed to generate code for Task {task.id}")

        elif task.type == TaskType.MEMORY:
            # Memory Agent scans the workspace
            logger.debug(f"Memory Agent scanning workspace for context...")
            files = self.toolbox.list_files(self.workspace) if os.path.exists(self.workspace) else []
            memory_prompt = f"Project Workspace contains: {files}. Scan and generate the Context Map."
            summary = self.llm.query(MEMORY_AGENT_SYSTEM_PROMPT, memory_prompt, response_format="json")
            
            if summary:
                task.output = summary
                task.status = TaskStatus.COMPLETED
                logger.info(f"Memory Agent updated context map. Tracked {len(files)} files.")
            else:
                task.status = TaskStatus.FAILED
                logger.error("Memory Agent failed to generate summary.")
        else:
            # Handle other task types
            logger.info(f"Completing [ {task.type.value} ] Task {task.id} automatically.")
            task.status = TaskStatus.COMPLETED
            task.output = f"Finished {task.type.value}"