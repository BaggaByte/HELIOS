# HELIOS

HELIOS is a local-first, AI-assisted cybersecurity platform designed to automate and augment penetration testing, vulnerability scanning, and threat modeling workflows. It provides an offline-capable, privacy-first alternative to cloud-based security agents.

## Project Structure

- `apps/web/` - React frontend UI (Zustand, Vite)
- `apps/desktop/` - Tauri desktop wrapper for running as a native app
- `services/` - FastAPI backend application (SQLAlchemy, Celery)

## Requirements

- Python 3.10+
- Node.js 18+
- Rust (for Tauri desktop app)
- Redis (for Celery background tasks)

## Configuration (.env)

Create a `.env` file in the `services/` directory to configure the backend. If you don't set a `SECRET_KEY`, one will be randomly generated each time you start the app.

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
OV_MODEL_PATH=./models/phi-4-mini-openvino
OV_DEVICE=AUTO

# Redis / Background Tasks
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
```

## Running the Application

### 1. Start the Backend

From the `services/` directory, ensure dependencies are installed (e.g. via `uv` or `pip`) and start the FastAPI server:

```bash
cd services
uv run uvicorn helios.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the Frontend / Desktop App

In a separate terminal window, start the frontend. You can run the web UI directly, or launch the Tauri desktop shell:

```bash
# To run the web app in your browser
cd apps/web
npm install
npm run dev

# OR to run the native desktop shell
cd apps/desktop
npm install
npm run tauri dev
```

## Architecture Notes

HELIOS operates fully offline and stores all knowledge locally. 
- **Knowledge Graph:** Findings, Hosts, and Services are automatically synced to an internal knowledge graph to build attack path context.
- **Background Tasks:** Reconnaissance plugins and heavy scans run asynchronously via Celery + Redis.
- **OpenVINO Acceleration:** If you have an NPU/GPU, HELIOS can leverage local LLMs for code analysis and finding summaries using Intel OpenVINO.
