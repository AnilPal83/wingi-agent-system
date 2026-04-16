from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from .logger import setup_logger

logger = setup_logger("Models")

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
                # Check if all dependencies are completed
                unmet_deps = [dep for dep in node.dependencies if self.nodes[dep].status != TaskStatus.COMPLETED]
                if not unmet_deps:
                    runnable.append(node)
                else:
                    logger.debug(f"Task {node.id} is blocked by: {unmet_deps}")
        
        if runnable:
            logger.info(f"Identified runnable tasks: {[t.id for t in runnable]}")
        return runnable