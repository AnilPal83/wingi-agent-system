# Wingi Agent System

An autonomous multi-agent orchestration framework prototype inspired by Emergent.

## Key Features

- **Live Gemini Integration**: Uses Google's Gemini 1.5 Pro for dynamic planning and coding.
- **Autonomous Planning**: Decomposes user goals into a Dynamic Task Graph.
- **Real Tool Execution**: Includes a ToolBox for file I/O and shell command execution.
- **Stateful Orchestration**: Manages task dependencies and execution cycles.
- **Web Dashboard**: Modern React UI to visualize agent progress.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AnilPal83/wingi-agent-system.git
   cd wingi-agent-system
   ```

2. Install dependencies:
   ```bash
   pip install google-generativeai python-dotenv pydantic fastapi uvicorn
   ```

3. Set up your environment variables:
   ```bash
   cp .env.example .env
   # Add your GOOGLE_API_KEY to .env
   ```

## Usage

### CLI Mode
```bash
python3 main.py
```

### Web Dashboard Mode
1. Start the server:
   ```bash
   python3 server.py
   ```
2. Run the UI (requires Node.js):
   ```bash
   cd ui && npm install && npm run dev
   ```
Go to `localhost:5173` in your browser.

## Project Structure

- `core/`: Core engine, Gemini client, and data models.
- `agents/`: System prompts for specialized roles.
- `tools/`: Registry for file and system tools.
- `ui/`: React TypeScript dashboard.
- `main.py`: CLI entry point.
- `server.py`: FastAPI WebSocket backend.