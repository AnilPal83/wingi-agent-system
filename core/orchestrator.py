from .models import TaskGraph, TaskNode, TaskStatus, TaskType
from .llm_client import LLMClient
from tools.registry import ToolBox
from agents.prompts import ORCHESTRATOR_SYSTEM_PROMPT, CODER_SYSTEM_PROMPT, MEMORY_AGENT_SYSTEM_PROMPT
import json
import os

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
        prompt = f"Goal: {self.user_goal}\n\nDecompose this into a valid JSON TaskGraph. Include a 'memory' task after architectural design to map the project. Output only the 'nodes' array."
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
                print("\n🏁 Project Complete.")
            return

        for task in runnable:
            self.execute_task(task)

    def execute_task(self, task: TaskNode):
        task.status = TaskStatus.RUNNING
        print(f"🚀 [AGENT: {task.type.value.upper()}] Working on: {task.description}...")

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

        elif task.type == TaskType.MEMORY:
            # Memory Agent scans the workspace
            files = self.toolbox.list_files(self.workspace) if os.path.exists(self.workspace) else []
            memory_prompt = f"Project Workspace contains: {files}. Scan and generate the Context Map."
            summary = self.llm.query(MEMORY_AGENT_SYSTEM_PROMPT, memory_prompt, response_format="json")
            
            if summary:
                task.output = summary
                task.status = TaskStatus.COMPLETED
                print(f"🧠 Memory Agent updated the context map for {len(files)} files.")
            else:
                task.status = TaskStatus.FAILED
        else:
            # Handle other task types
            task.status = TaskStatus.COMPLETED
            task.output = f"Finished {task.type.value}"