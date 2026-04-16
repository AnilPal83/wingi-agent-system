# 🚀 Wingi Agent System

An autonomous multi-agent orchestration framework prototype inspired by Emergent. This system allows you to build entire applications from a single prompt by orchestrating a team of specialized AI agents.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.10+**
- **Node.js & npm** (for the Web Dashboard)
- **Google Cloud SDK (gcloud)** (Optional, for authentication)
- **Poetry** (Python dependency manager)

---

## 📥 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AnilPal83/wingi-agent-system.git
   cd wingi-agent-system
   ```

2. **Install Python dependencies:**
   ```bash
   poetry install
   ```

3. **Install UI dependencies:**
   ```bash
   cd ui
   npm install
   cd ..
   ```

---

## ⚙️ Configuration

1. **Create your environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** and add your Google Cloud Project ID:
   ```env
   VERTEX_PROJECT_ID=your-project-id-here
   VERTEX_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
   ```

3. **Authenticate with Google Cloud (Option A - Recommended):**
   Place your Service Account JSON key in the root folder and set the path in `.env`.

   **Option B (Individual):**
   Run `gcloud auth application-default login`.

---

## 🚀 Running the System

### Option A: Web Dashboard (Recommended)
This gives you a visual view of the agent's task graph and real-time logs.

1. **Start the Backend:**
   ```bash
   poetry run python server.py
   ```

2. **Start the Frontend (in a new terminal):**
   ```bash
   cd ui
   npm run dev
   ```
3. Open **http://localhost:5173** in your browser.

### Option B: CLI Mode
For a fast, terminal-only experience.
```bash
poetry run python main.py
```

---

## 🏗️ Architecture

- **Orchestrator**: The central brain managing the Task Graph.
- **Planner Agent**: Decomposes goals into actionable steps.
- **Architect Agent**: Designs the tech stack and schemas.
- **Coder Agent**: Implements the actual code.
- **Memory Agent**: Indexes the project to maintain a "Context Map".
- **Verifier Agent**: Runs tests and validates the output.

---

## 📁 Project Structure

- `core/`: State machine, Vertex AI client, and data models.
- `agents/`: Specialized system prompts for each role.
- `tools/`: The "hands" (File I/O and Shell tools).
- `ui/`: React TypeScript dashboard.
- `server.py`: FastAPI WebSocket server.

---

## 📝 Debugging

The system outputs emoji-enriched logs to help you follow the agent's thoughts:
- ✨ **INFO**: General progress updates.
- 🔍 **DEBUG**: Internal reasoning and task transitions.
- ❌ **ERROR**: API issues or task failures.