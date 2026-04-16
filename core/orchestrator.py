from .models import TaskGraph, TaskNode, TaskStatus, TaskType
from typing import List, Dict, Optional, Any
import time
import os

class Orchestrator:
    def __init__(self, project_name: str, user_goal: str):
        self.graph = TaskGraph(project_name=project_name)
        self.user_goal = user_goal
        self.is_running = True
        self.workspace = "/root/workspace/generated_app"

    def update_task_status(self, task_id: str, status: TaskStatus, output: Any = None):
        if task_id in self.graph.nodes:
            node = self.graph.nodes[task_id]
            node.status = status
            node.output = output
            print(f"📊 Task {task_id}: {status}")

    def run_cycle(self):
        runnable_tasks = self.graph.get_runnable_tasks()
        if not runnable_tasks:
            if all(n.status == TaskStatus.COMPLETED for n in self.graph.nodes.values()) and self.graph.nodes:
                print("\n🏁 PROJECT COMPLETE: Fullstack App is ready in /generated_app")
                self.is_running = False
                return
            return

        for task in runnable_tasks:
            self.dispatch_task(task)

    def dispatch_task(self, task: TaskNode):
        task.status = TaskStatus.RUNNING
        print(f"🚀 [AGENT: {task.type.value.upper()}] Working on: {task.description}...")
        
        # Simulated Agent logic that actually creates files
        if task.type == TaskType.CODE:
            filename = task.input_context.get("filename", "output.txt")
            content = task.input_context.get("content", "// Placeholder")
            
            filepath = os.path.join(self.workspace, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(content)
            
            result = f"Created {filename}"
        else:
            time.sleep(0.5)
            result = f"Completed {task.type.value}"

        self.update_task_status(task.id, TaskStatus.COMPLETED, result)