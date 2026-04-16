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
        self.workspace = os.path.join(os.getcwd(), "workspace", project_name)
        
        self.project_id = self.db.create_project(project_name, user_goal)
        logger.info(f"Initialized Orchestrator. Project ID: {self.project_id}")

    # Maps common model hallucinations to valid TaskType values
    _TYPE_ALIASES = {
        "design": "architect",
        "architecture": "architect",
        "coding": "code",
        "implementation": "code",
        "implement": "code",
        "testing": "test",
        "verification": "validate",
        "deployment": "deploy",
        "setup": "plan",
        "planning": "plan",
    }

    def bootstrap_plan(self):
        logger.info(f"Planning the project based on goal: '{self.user_goal}'")
        valid_types = ", ".join(f'"{t.value}"' for t in TaskType)
        prompt = (
            f"Goal: {self.user_goal}\n\n"
            "Decompose this into a valid JSON TaskGraph. "
            "Include a 'memory' task after architectural design to map the project. "
            f"Each node's 'type' field MUST be one of: {valid_types}. "
            "Required node fields: id (string), type (one of the values above), "
            "description (string), dependencies (array of id strings). "
            'Return a JSON object: {"nodes": [ ... ]}'
        )
        plan = self.llm.query(ORCHESTRATOR_SYSTEM_PROMPT, prompt, response_format="json")

        # Model sometimes returns a bare array instead of {"nodes": [...]}
        if isinstance(plan, list):
            plan = {"nodes": plan}

        if plan and "nodes" in plan:
            for node_data in plan["nodes"]:
                # Normalise type aliases the model may invent
                raw_type = node_data.get("type", "")
                node_data["type"] = self._TYPE_ALIASES.get(raw_type, raw_type)
                node = TaskNode(**node_data)
                self.graph.nodes[node.id] = node

            self.db.log_event(self.project_id, "PLAN_GENERATED", data={"nodes": plan["nodes"]})
            logger.info(f"Created Task Graph with {len(self.graph.nodes)} nodes.")
        else:
            logger.error(f"Failed to bootstrap the initial plan. LLM returned: {plan!r}")
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
            coder_prompt = (
                f"Task: {task.description}\nContext: {task.input_context}\n"
                "Write the code and return it as JSON. "
                "If multiple files are needed return an array: "
                '[{"filename": "path/to/file.py", "content": "..."}]. '
                'If only one file, you may return a single object: {"filename": "...", "content": "..."}.'
            )
            result = self.llm.query(CODER_SYSTEM_PROMPT, coder_prompt, response_format="json")

            if result:
                # Normalise: single dict → list of one
                files = result if isinstance(result, list) else [result]
                written = []
                for f in files:
                    path = f"{self.workspace}/{f['filename']}"
                    self.toolbox.write_file(path, f['content'])
                    written.append(f['filename'])
                    logger.info(f"Coder Agent wrote {f['filename']}.")
                task.status = TaskStatus.COMPLETED
                task.output = {"files": written}
                self.db.log_event(self.project_id, "TASK_COMPLETED", task_id=task.id, data=task.dict())
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