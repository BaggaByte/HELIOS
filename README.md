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

### 1. Start the Web App

After installing the backend dependencies with `cd services; uv sync`, return to the repository root and start the frontend and backend together. The launcher picks an available local API port, so it still works when another service already uses port 8000.

```bash
npm install
npm run dev
# Open http://localhost:3000
```

### 2. Start the Desktop App

The Tauri shell starts its backend automatically. Install backend dependencies first; AI inference dependencies are optional.

```bash
cd services
uv sync
cd ../apps/desktop
cargo tauri dev
```

To run the API alone for another client, start it from `services/` with `uv run uvicorn helios.main:app --host 127.0.0.1 --port 8000 --reload`.

## Architecture Notes

HELIOS stores project data locally. AI chat returns a clearly marked mock response when the OpenVINO model is not loaded.
- **Knowledge Graph:** Findings, Hosts, and Services are automatically synced to an internal knowledge graph to build attack path context.
- **Reconnaissance:** Nmap scans run in a worker thread in the local API process and persist results to the selected project. Other scanner integrations are disabled for the first release.
- **OpenVINO Acceleration:** If you have an NPU/GPU, HELIOS can leverage local LLMs for code analysis and finding summaries using Intel OpenVINO.
