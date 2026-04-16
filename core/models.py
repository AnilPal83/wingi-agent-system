from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class TaskType(str, Enum):
    PLAN = "plan"
    ARCHITECT = "architect"
    MEMORY = "memory"
    CODE = "code"
    TEST = "test"
    VALIDATE = "validate"
    DEPLOY = "deploy"

class TaskNode(BaseModel):
    id: str
    type: TaskType
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = []
    input_context: Dict[str, Any] = {}
    output: Optional[Any] = None
    retry_count: int = 0
    max_retries: int = 3
    agent_assigned: Optional[str] = None

class TaskGraph(BaseModel):
    project_name: str
    nodes: Dict[str, TaskNode] = {}
    
    def get_runnable_tasks(self) -> List[TaskNode]:
        """Finds tasks that have no dependencies or whose dependencies are COMPLETED."""
        runnable = []
        for node in self.nodes.values():
            if node.status == TaskStatus.PENDING:
                if all(self.nodes[dep].status == TaskStatus.COMPLETED for dep in node.dependencies):
                    runnable.append(node)
        return runnable