from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.orchestrator import Orchestrator
from core.models import TaskStatus
from core.logger import setup_logger
import asyncio
import json

app = FastAPI()
logger = setup_logger("Server")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async list_connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Remaining connections: {len(self.active_connections)}")

    async send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.list_connect(websocket)
    orchestrator = None
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.info(f"Message received via WebSocket: {message['type']}")
            
            if message["type"] == "START_PROJECT":
                goal = message["goal"]
                logger.info(f"Starting Project: '{goal}'")
                orchestrator = Orchestrator(project_name="WebProject", user_goal=goal)
                
                await websocket.send_json({"type": "LOG", "content": f"🎯 Goal received: {goal}"})
                
                # Run planning in background
                orchestrator.bootstrap_plan()
                await websocket.send_json({
                    "type": "GRAPH_UPDATE", 
                    "nodes": [n.dict() for n in orchestrator.graph.nodes.values()]
                })

                # Start execution loop
                while orchestrator.is_running:
                    runnable = orchestrator.graph.get_runnable_tasks()
                    if not runnable:
                        if all(n.status == TaskStatus.COMPLETED for n in orchestrator.graph.nodes.values()):
                            orchestrator.is_running = False
                        await asyncio.sleep(1)
                        continue

                    for task in runnable:
                        await websocket.send_json({"type": "LOG", "content": f"🚀 Starting task: {task.description}"})
                        orchestrator.execute_task(task)
                        
                        # Send graph update after each task
                        await websocket.send_json({
                            "type": "GRAPH_UPDATE", 
                            "nodes": [n.dict() for n in orchestrator.graph.nodes.values()]
                        })
                
                await websocket.send_json({"type": "LOG", "content": "🏁 Project Complete!"})

            elif message["type"] == "CHAT":
                # Handle direct chat interaction here
                await websocket.send_json({"type": "LOG", "content": f"💬 You said: {message['content']}"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Wingi Server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)