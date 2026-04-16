import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, CheckCircle2, Circle, Loader2, LayoutGrid, Terminal } from 'lucide-react';

interface Task {
  id: string;
  type: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

interface Message {
  role: 'agent' | 'user';
  content: string;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'agent', content: "Hello! I'm your Wingi Agent. What application would you like me to build today?" }
  ]);
  const [input, setInput] = useState('');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/ws');
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'LOG') {
        setMessages(prev => [...prev, { role: 'agent', content: data.content }]);
      } else if (data.type === 'GRAPH_UPDATE') {
        setTasks(data.nodes);
      }
    };
    setWs(socket);
    return () => socket.close();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || !ws) return;
    if (tasks.length === 0) {
      ws.send(JSON.stringify({ type: 'START_PROJECT', goal: input }));
    } else {
      ws.send(JSON.stringify({ type: 'CHAT', content: input }));
    }
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    setInput('');
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200">
      <div className="w-80 border-r border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-6">
        <div className="flex items-center gap-2 font-bold text-xl text-blue-400">
          <LayoutGrid size={24} />
          <span>Task Graph</span>
        </div>
        <div className="flex-1 overflow-y-auto space-y-4">
          {tasks.length === 0 ? (
            <div className="text-slate-500 text-sm italic">No tasks active. Start a project to see the graph.</div>
          ) : (
            tasks.map(task => (
              <div key={task.id} className="p-3 rounded-lg border border-slate-800 bg-slate-900 flex items-start gap-3">
                <div className="mt-1">
                  {task.status === 'completed' && <CheckCircle2 className="text-green-500" size={18} />}
                  {task.status === 'running' && <Loader2 className="text-blue-500 animate-spin" size={18} />}
                  {task.status === 'pending' && <Circle className="text-slate-600" size={18} />}
                </div>
                <div>
                  <div className="text-xs font-mono text-slate-500 uppercase tracking-tighter">{task.id} - {task.type}</div>
                  <div className="text-sm">{task.description}</div>
                </div>
              </div>
            ))
          )}
        </div>
        <div className="pt-4 border-t border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-500">
                <Terminal size={14} />
                <span>Backend: localhost:8000</span>
            </div>
        </div>
      </div>
      <div className="flex-1 flex flex-col relative">
        <header className="h-16 border-b border-slate-800 flex items-center px-8 bg-slate-950/80 backdrop-blur-md sticky top-0 z-10">
          <h2 className="font-semibold text-lg flex items-center gap-2">
             <div className="w-2 h-2 rounded-full bg-green-500"></div>
             Wingi Orchestrator
          </h2>
        </header>
        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex gap-4 max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'agent' ? 'bg-blue-600' : 'bg-slate-700'}`}>
                  {msg.role === 'agent' ? <Bot size={20} /> : <User size={20} />}
                </div>
                <div className={`p-4 rounded-2xl ${msg.role === 'agent' ? 'bg-slate-900 border border-slate-800' : 'bg-blue-700 text-white'}`}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          <div ref={scrollRef} />
        </div>
        <div className="p-8">
          <div className="max-w-4xl mx-auto relative">
            <input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Send a goal or a message..."
              className="w-full bg-slate-900 border border-slate-800 rounded-2xl py-4 px-6 pr-16 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
            <button 
              onClick={handleSend}
              className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center hover:bg-blue-500 transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}