from .models import TaskGraph, TaskNode, TaskStatus, TaskType
from .llm_client import LLMClient
from .logger import setup_logger
from .database import DBManager
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
        self.db = DBManager()
        self.is_running = True
        self.workspace = f"/root/workspace/{project_name}"
        
        self.project_id = self.db.create_project(project_name, user_goal)
        logger.info(f"Initialized Orchestrator. Project ID: {self.project_id}")

    def bootstrap_plan(self):
        logger.info(f"Planning the project based on goal: '{self.user_goal}'")
        prompt = f"Goal: {self.user_goal}\n\nDecompose this into a valid JSON TaskGraph. Include a 'memory' task after architectural design to map the project. Output only the 'nodes' array."
        plan = self.llm.query(ORCHESTRATOR_SYSTEM_PROMPT, prompt, response_format="json")
        
        if plan and "nodes" in plan:
            for node_data in plan["nodes"]:
                node = TaskNode(**node_data)
                self.graph.nodes[node.id] = node
            
            self.db.log_event(self.project_id, "PLAN_GENERATED", data={"nodes": plan["nodes"]})
            logger.info(f"Created Task Graph with {len(self.graph.nodes)} nodes.")
        else:
            logger.error("Failed to bootstrap the initial plan.")
            self.is_running = False

    def run_cycle(self):
        runnable = self.graph.get_runnable_tasks()
        if not runnable:
            if all(n.status == TaskStatus.COMPLETED for n in self.graph.nodes.values()) and self.graph.nodes:
                self.is_running = False
                self.db.log_event(self.project_id, "PROJECT_FINISHED")
                print("\n🏁 Project Complete.")
            return

        for task in runnable:
            self.execute_task(task)

    def execute_task(self, task: TaskNode):
        task.status = TaskStatus.RUNNING
        self.db.log_event(self.project_id, "TASK_START", task_id=task.id, data=task.dict())
        logger.info(f"Executing [ {task.type.value.upper()} ] Task {task.id}: '{task.description}'...")

        if task.type == TaskType.CODE:
            coder_prompt = f"Task: {task.description}\nContext: {task.input_context}\nWrite the code and return it as JSON: {{'filename': '...', 'content': '...'}}"
            result = self.llm.query(CODER_SYSTEM_PROMPT, coder_prompt, response_format="json")
            
            if result:
                path = f"{self.workspace}/{result['filename']}"
                status = self.toolbox.write_file(path, result['content'])
                task.status = TaskStatus.COMPLETED
                task.output = {"status": status, "filename": result['filename']}
                self.db.log_event(self.project_id, "TASK_COMPLETED", task_id=task.id, data=task.dict())
                logger.info(f"Coder Agent successfully generated {result['filename']}.")
            else:
                task.status = TaskStatus.FAILED
                self.db.log_event(self.project_id, "TASK_FAILED", task_id=task.id, data={"error": "LLM returned no result"})

        elif task.type == TaskType.MEMORY:
            files = self.toolbox.list_files(self.workspace) if os.path.exists(self.workspace) else []
            memory_prompt = f"Project Workspace contains: {files}. Scan and generate the Context Map."
            summary = self.llm.query(MEMORY_AGENT_SYSTEM_PROMPT, memory_prompt, response_format="json")
            
            if summary:
                task.output = summary
                task.status = TaskStatus.COMPLETED
                self.db.log_event(self.project_id, "TASK_COMPLETED", task_id=task.id, data=task.dict())
                logger.info(f"Memory Agent updated context map.")
            else:
                task.status = TaskStatus.FAILED
                self.db.log_event(self.project_id, "TASK_FAILED", task_id=task.id, data={"error": "Memory Agent failed"})
        else:
            task.status = TaskStatus.COMPLETED
            task.output = f"Finished {task.type.value}"
            self.db.log_event(self.project_id, "TASK_COMPLETED", task_id=task.id, data=task.dict())