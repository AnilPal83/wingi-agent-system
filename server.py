from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from core.orchestrator import Orchestrator
from core.models import TaskStatus
from core.logger import setup_logger
from core.database import DBManager, ProjectRecord, EventRecord
import asyncio
import json

app = FastAPI()
logger = setup_logger("Server")
db_manager = DBManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/history/{project_id}")
async def get_project_history(project_id: int):
    history = db_manager.get_history(project_id)
    return {"history": [h.data for h in history if h.data]}

@app.get("/inspector", response_class=HTMLResponse)
async def project_inspector():
    """A dedicated visualizer for the project memory on port 8000/inspector"""
    projects = db_manager.db.query(ProjectRecord).all()
    
    html_content = """
    <html>
        <head>
            <title>Wingi Project Inspector</title>
            <script src=\"https://cdn.tailwindcss.com\"></script>
        </head>
        <body class=\"bg-slate-950 text-slate-200 p-10 font-sans\">
            <h1 class=\"text-3xl font-bold text-blue-400 mb-8\">🔍 Wingi Memory Inspector</h1>
            <div class=\"space-y-8\">
    """
    
    for p in projects:
        events = db_manager.get_history(p.id)
        html_content += f"""
            <div class=\"bg-slate-900 border border-slate-800 rounded-xl p-6\">
                <div class=\"flex justify-between items-center mb-4\">
                    <h2 class=\"text-xl font-semibold text-white\">Project: {p.name}</h2>
                    <span class=\"text-xs text-slate-500\">{p.created_at.strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
                <p class=\"text-sm text-slate-400 mb-6 italic\">Goal: {p.goal}</p>
                <div class=\"space-y-4 border-l-2 border-slate-800 ml-4\">"""
        for e in events:
            color = "blue"
            if "COMPLETED" in e.event_type: color = "green"
            if "FAILED" in e.event_type: color = "red"
            
            html_content += f"""
                    <div class=\"relative pl-6\">
                        <div class=\"absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-slate-800 border-2 border-slate-950\"></div>
                        <div class=\"text-xs font-bold text-{color}-400 uppercase\">{e.event_type}</div>
                        <div class=\"text-sm text-slate-300\">{e.task_id if e.task_id else 'System'} - {e.timestamp.strftime('%H:%M:%S')}</div>
                    </div>"""
        html_content += "</div></div>"
        
    html_content += "</div></body></html>"
    return html_content

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
                orchestrator = Orchestrator(project_name=\"WebProject\", user_goal=goal)
                await websocket.send_json({"type": "PROJECT_STARTED", "project_id": orchestrator.project_id})
                await websocket.send_json({"type": "LOG", "content": f"\ud83c\udfaf Goal received: {goal}"})
                
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
                        await websocket.send_json({"type": "LOG", "content": f"\ud83d\ude80 Starting task: {task.description}"})
                        orchestrator.execute_task(task)
                        await websocket.send_json({
                            "type": "GRAPH_UPDATE", 
                            "nodes": [n.dict() for n in orchestrator.graph.nodes.values()]
                        })
                
                await websocket.send_json({"type": "LOG", "content": "\ud83c\udfc1 Project Complete!"})

            elif message["type"] == "CHAT":
                await websocket.send_json({"type": "LOG", "content": f"\ud83d\udcac You said: {message['content']}"})

    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)