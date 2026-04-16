import unittest
import os
import shutil
from core.models import TaskGraph, TaskNode, TaskStatus, TaskType
from core.orchestrator import Orchestrator
from tools.registry import ToolBox

class TestAgentSystem(unittest.TestCase):
    def setUp(self):
        self.test_workspace = "/root/workspace/MyGeneratedApp"
        if os.path.exists(self.test_workspace):
            shutil.rmtree(self.test_workspace)

    def test_graph_dependencies(self):
        from core.models import TaskGraph, TaskNode, TaskType, TaskStatus
        graph = TaskGraph(project_name="TestProject")
        t1 = TaskNode(id="T1", type=TaskType.PLAN, description="Task 1")
        t2 = TaskNode(id="T2", type=TaskType.CODE, description="Task 2", dependencies=["T1"])
        graph.nodes = {"T1": t1, "T2": t2}
        
        runnable = graph.get_runnable_tasks()
        assert len(runnable) == 1
        assert runnable[0].id == "T1"
        
        t1.status = TaskStatus.COMPLETED
        runnable = graph.get_runnable_tasks()
        assert runnable[0].id == "T2"

    def test_toolbox_file_io(self):
        toolbox = ToolBox()
        path = "/root/workspace/MyGeneratedApp/test.txt"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        result = toolbox.write_file(path, "Hello World")
        assert os.path.exists(path)
        with open(path, "r") as f:
            assert f.read() == "Hello World"

if __name__ == "__main__":
    unittest.main()