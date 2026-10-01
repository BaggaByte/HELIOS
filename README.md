# HELIOS

HELIOS is a local-first, AI-assisted cybersecurity platform designed to automate and augment penetration testing, vulnerability scanning, and threat modeling workflows. It provides an offline-capable, privacy-first alternative to cloud-based security agents.

## Project Structure

- `apps/web/` - React frontend UI (Zustand, Vite)
- `apps/desktop/` - Tauri desktop wrapper for running as a native app
- `services/` - FastAPI backend application (SQLAlchemy, Celery)

## Requirements

- Python 3.13+
- Node.js 20.19+ (required by Vite 8)
- Rust (for Tauri desktop app)
- Nmap (for live network scans; keep scans within the selected project's authorized scope)

## Configuration (.env)

Copy the root `.env.example` to `.env` in the repository root. If you don't set a `SECRET_KEY`, one will be randomly generated each time you start the app.

```env
# Core Application
APP_NAME=HELIOS
DEBUG=True
SECRET_KEY=your-secure-random-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./helios.db

# Storage & Models
CHROMA_PERSIST_DIR=./data/chroma
UPLOAD_DIR=./data/uploads

# AI / OpenVINO (Optional)
OV_MODEL_PATH=../models/phi4_mini_int4_ov
OV_DEVICE=AUTO
```

## Running the Application

### 1. Start the Backend

From the `services/` directory, install the pinned backend dependencies and start the FastAPI server. The AI inference dependencies are optional to keep the core lightweight; install them using the `ai` extra if you want local models.

```bash
cd services
# Install with AI dependencies
uv sync --extra ai
uv run uvicorn helios.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the Frontend / Desktop App

In a separate terminal window, install the root npm workspace dependencies and start the frontend. The desktop shell uses the same web workspace. Start the backend separately before using either UI.

```bash
# From the repository root
npm install
npm run dev

# To run the native desktop shell (requires the Tauri CLI and Rust)
cd apps/desktop
cargo tauri dev
```

## Architecture Notes

HELIOS stores project data locally. AI chat returns a clearly marked mock response when the OpenVINO model is not loaded.
- **Knowledge Graph:** Findings, Hosts, and Services are automatically synced to an internal knowledge graph to build attack path context.
- **Reconnaissance:** Nmap scans run in a worker thread in the local API process and persist results to the selected project. Other scanner integrations are disabled for the first release.
- **OpenVINO Acceleration:** If you have an NPU/GPU, HELIOS can leverage local LLMs for code analysis and finding summaries using Intel OpenVINO.
