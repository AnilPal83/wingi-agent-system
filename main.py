from core.orchestrator import Orchestrator
from core.models import TaskNode, TaskType, TaskStatus
import json

def main():
    prompt = "Build a fullstack todo app with Node.js backend and React frontend."
    print(f"🚀 USER PROMPT: '{prompt}'\n")
    
    orchestrator = Orchestrator(project_name="FullstackApp", user_goal=prompt)

    # --- SIMULATING THE PLANNER AGENT'S DYNAMIC DECOMPOSITION ---
    # In a production system, this JSON would come from an LLM call.
    print("🧠 PLANNER AGENT: Decomposing goal into tasks...")
    
    plan_json = [
        {"id": "T1", "type": "plan", "description": "Initialize project structure and manifest."},
        {"id": "T2", "type": "architect", "description": "Define API routes and DB schema.", "dependencies": ["T1"]},
        {"id": "T3", "type": "code", "description": "Create Express.js server.", "dependencies": ["T2"], 
         "input_context": {"filename": "server.js", "content": "const express = require('express');\nconst app = express();\napp.use(express.json());\nlet todos = [];\napp.get('/todos', (req, res) => res.json(todos));\napp.post('/todos', (req, res) => { todos.push(req.body); res.send('Added'); });\napp.listen(5000);"}},
        {"id": "T4", "type": "code", "description": "Create React App component.", "dependencies": ["T2"],
         "input_context": {"filename": "App.js", "content": "import React from 'react';\nexport default function App() { return <h1>Todo List</h1>; }"}},
        {"id": "T5", "type": "test", "description": "Run integration tests.", "dependencies": ["T3", "T4"]}
    ]

    # Injecting the dynamic plan into the Orchestrator
    for t_data in plan_json:
        task = TaskNode(**t_data)
        orchestrator.graph.nodes[task.id] = task

    # 2. RUN THE ENGINE
    print("\n⚙️ ENGINE STARTING...")
    while orchestrator.is_running:
        orchestrator.run_cycle()

if __name__ == "__main__":
    main()