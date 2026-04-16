from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.orchestrator import Orchestrator
from core.models import TaskStatus
from core.logger import setup_logger
from core.database import DBManager
import asyncio
import json

app = FastAPI()
logger = setup_logger("Server")
db = DBManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/history/{project_id}")
async def get_project_history(project_id: int):
    history = db.get_history(project_id)
    return {"history": [h.data for h in history if h.data]}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    orchestrator = None
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "START_PROJECT":
                goal = message["goal"]
                orchestrator = Orchestrator(project_name="WebProject", user_goal=goal)
                
                await websocket.send_json({"type": "PROJECT_STARTED", "project_id": orchestrator.project_id})
                await websocket.send_json({"type": "LOG", "content": f"🎯 Goal received: {goal}"})
                
                orchestrator.bootstrap_plan()
                await websocket.send_json({
                    "type": "GRAPH_UPDATE", 
                    "nodes": [n.dict() for n in orchestrator.graph.nodes.values()]
                })

                while orchestrator.is_running:
                    runnable = orchestrator.graph.get_runnable_tasks()
                    if not runnable:
                        if all(n.status == TaskStatus.COMPLETED for n in orchestrator.graph.nodes.values()) and orchestrator.graph.nodes:
                            orchestrator.is_running = False
                        await asyncio.sleep(1)
                        continue

                    for task in runnable:
                        await websocket.send_json({"type": "LOG", "content": f"🚀 Starting task: {task.description}"})
                        orchestrator.execute_task(task)
                        await websocket.send_json({
                            "type": "GRAPH_UPDATE", 
                            "nodes": [n.dict() for n in orchestrator.graph.nodes.values()]
                        })
                
                await websocket.send_json({"type": "LOG", "content": "🏁 Project Complete!"})

            elif message["type"] == "CHAT":
                await websocket.send_json({"type": "LOG", "content": f"💬 You said: {message['content']}"})

    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)