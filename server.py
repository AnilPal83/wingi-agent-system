from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.orchestrator import Orchestrator
from core.models import TaskStatus
import asyncio
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "START_PROJECT":
                goal = message["goal"]
                orchestrator = Orchestrator(project_name="WebProject", user_goal=goal)
                await websocket.send_json({"type": "LOG", "content": f"🎯 Goal received: {goal}"})
                
                await asyncio.to_thread(orchestrator.bootstrap_plan)
                await websocket.send_json({
                    "type": "GRAPH_UPDATE", 
                    "nodes": [n.dict() for n in orchestrator.graph.nodes.values()]
                })

                while orchestrator.is_running:
                    runnable = orchestrator.graph.get_runnable_tasks()
                    if not runnable:
                        if all(n.status == TaskStatus.COMPLETED for n in orchestrator.graph.nodes.values()):
                            orchestrator.is_running = False
                        await asyncio.sleep(1)
                        continue

                    for task in runnable:
                        await websocket.send_json({"type": "LOG", "content": f"🚀 Starting task: {task.description}"})
                        await asyncio.to_thread(orchestrator.execute_task, task)
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