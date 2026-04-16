from .models import TaskGraph, TaskNode, TaskStatus, TaskType
from .llm_client import LLMClient
from tools.registry import ToolBox
from agents.prompts import ORCHESTRATOR_SYSTEM_PROMPT, CODER_SYSTEM_PROMPT
import json

class Orchestrator:
    def __init__(self, project_name: str, user_goal: str):
        self.graph = TaskGraph(project_name=project_name)
        self.user_goal = user_goal
        self.llm = LLMClient()
        self.toolbox = ToolBox()
        self.is_running = True
        self.workspace = f"/root/workspace/{project_name}"

    def bootstrap_plan(self):
        """Asks the Planner LLM to generate the initial graph."""
        print("🧠 Planning the project...")
        prompt = f"Goal: {self.user_goal}\n\nDecompose this into a valid JSON TaskGraph. Output only the 'nodes' array."
        plan = self.llm.query(ORCHESTRATOR_SYSTEM_PROMPT, prompt, response_format="json")
        
        if plan and "nodes" in plan:
            for node_data in plan["nodes"]:
                node = TaskNode(**node_data)
                self.graph.nodes[node.id] = node
            print(f"📊 Created {len(self.graph.nodes)} tasks.")
        else:
            print("❌ Failed to create plan.")
            self.is_running = False

    def run_cycle(self):
        runnable = self.graph.get_runnable_tasks()
        if not runnable:
            if all(n.status == TaskStatus.COMPLETED for n in self.graph.nodes.values()):
                self.is_running = False
                print("🏁 Project Complete.")
            return

        for task in runnable:
            self.execute_task(task)

    def execute_task(self, task: TaskNode):
        task.status = TaskStatus.RUNNING
        print(f"🚀 Working on: {task.description}...")

        if task.type == TaskType.CODE:
            # Get implementation from Coder Agent
            coder_prompt = f"Task: {task.description}\nContext: {task.input_context}\nWrite the code and return it as JSON: {{'filename': '...', 'content': '...'}}"
            result = self.llm.query(CODER_SYSTEM_PROMPT, coder_prompt, response_format="json")
            
            if result:
                path = f"{self.workspace}/{result['filename']}"
                status = self.toolbox.write_file(path, result['content'])
                task.status = TaskStatus.COMPLETED
                task.output = status
                print(status)
            else:
                task.status = TaskStatus.FAILED
        else:
            # Handle other task types
            task.status = TaskStatus.COMPLETED
            task.output = "Task finished (Simulated for non-code tasks)"
