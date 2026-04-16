# Wingi Agent System

An autonomous multi-agent orchestration framework prototype inspired by Emergent.

## Architecture

This system uses a **Hierarchical Multi-Agent Architecture** with a **Dynamic Task Graph** at its core.

- **Orchestrator**: Manages the state and routing of tasks.
- **Planner Agent**: Decomposes high-level goals into atomic tasks.
- **Architect Agent**: Designs technical specs and schemas.
- **Coder Agent**: Implements the code in a scoped environment.
- **Verifier Agent**: Validates code via testing and static analysis.

## Project Structure

- `core/`: Contains the base models (`models.py`) and the orchestration engine (`orchestrator.py`).
- `agents/`: Contains system prompts for specialized roles.
- `main.py`: The entry point to bootstrap and run the system.

## Usage

Run the system with:
```bash
python3 main.py
```