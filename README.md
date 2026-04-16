# Wingi Agent System

An autonomous multi-agent orchestration framework prototype inspired by Emergent.

## Key Features

- **Live Gemini Integration**: Supports both Google AI Studio and **Vertex AI** (Enterprise).
- **Autonomous Planning**: Decomposes user goals into a Dynamic Task Graph.
- **Real Tool Execution**: Includes a ToolBox for file I/O and shell command execution.
- **Stateful Orchestration**: Manages task dependencies and execution cycles.
- **Web Dashboard**: Modern React UI to visualize agent progress.
- **Structured Logging**: Emoji-enriched debugging logs for full transparency.

## Installation

We use `pyproject.toml` for modern dependency management.

1. Clone the repository:
   ```bash
   git clone https://github.com/AnilPal83/wingi-agent-system.git
   cd wingi-agent-system
   ```

2. Install the package and dependencies:
   ```bash
   pip install .
   ```

3. Set up your environment variables:
   ```bash
   cp .env.example .env
   # Add your VERTEX_PROJECT_ID or GOOGLE_API_KEY to .env
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

- `core/`: Core engine, Gemini/Vertex clients, and data models.
- `agents/`: System prompts for specialized roles.
- `tools/`: Registry for file and system tools.
- `ui/`: React TypeScript dashboard.
- `main.py`: CLI entry point.
- `server.py`: FastAPI WebSocket backend.