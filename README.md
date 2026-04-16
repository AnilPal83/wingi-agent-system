# Wingi Agent System

An autonomous multi-agent orchestration framework inspired by Emergent.

## Key Features

- **Live LLM Integration**: Uses GPT-4 (or other models) for dynamic planning and coding.
- **Autonomous Planning**: Decomposes user goals into a Dynamic Task Graph.
- **Real Tool Execution**: Includes a ToolBox for file I/O and shell command execution.
- **Stateful Orchestration**: Manages task dependencies and execution cycles.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AnilPal83/wingi-agent-system.git
   cd wingi-agent-system
   ```

2. Install dependencies:
   ```bash
   pip install openai python-dotenv pydantic
   ```

3. Set up your environment variables:
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY to .env
   ```

## Usage

Run the system with:
```bash
python3 main.py
```
Enter your goal (e.g., "Build a fullstack todo app") and watch the agents work.

## Project Structure

- `core/`: Core engine, LLM client, and data models.
- `agents/`: System prompts for specialized roles.
- `tools/`: Registry for file and system tools.
- `main.py`: Entry point for the autonomous loop.