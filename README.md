# HELIOS - AI-Powered Offensive Security Copilot

HELIOS is a local-first, AI-assisted cybersecurity platform designed to automate and augment penetration testing, vulnerability scanning, and threat modeling workflows. It provides an offline-capable, privacy-first alternative to cloud-based security agents, ensuring zero telemetry and maximum operational security.

## 🚀 Key Features

*   **Offline-First Architecture**: Runs entirely locally without external AI dependencies, ensuring sensitive project data never leaves your environment.
*   **Knowledge Graph Engine**: Automatically correlates findings, hosts, and services across the entire attack surface.
*   **Reconnaissance Engine**: Native integration with 17+ industry-standard tools (Masscan, HTTPx, Amass, DNSx, Katana, Nuclei, etc.) via background task processing.
*   **Web Security & DAST Hub**: Dynamic web app security audit, HTTP request repeater, JWT analysis workbench, and ZAP/Burp XML ingestion.
*   **Source Code & Malware Analysis**: Deep static analysis using local RAG, Yara signature scanning, and LIEF binary analysis.
*   **AI-Augmented Reasoning**: Leverages Intel Core Ultra (OpenVINO) with on-device LLMs (e.g., Phi-4 Mini) for intelligent finding summarization, chat interactions, and code analysis.

## 🏗️ Technology Stack

*   **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Zustand, TanStack Query, React Flow.
*   **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Celery, Redis.
*   **AI & Inference**: OpenVINO, ChromaDB, SentenceTransformers.
*   **Desktop Shell (Optional)**: Tauri (Rust) for a native Windows 11 experience.

## 🛠️ Prerequisites

*   **Python 3.10+** (Recommended to use [uv](https://github.com/astral-sh/uv) for fast package management)
*   **Node.js 18+** & npm
*   **Rust** (Only if building the Tauri desktop application)
*   **Redis** (Required for background task processing via Celery)
*   *Security Tools*: Ensure binaries like `masscan`, `httpx`, `nuclei`, etc., are available in your system `PATH` if you plan to run live recon scans.

## ⚙️ Configuration

Create a `.env` file in the `services/` directory:

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

# AI / OpenVINO (Optional - Set OV_DEVICE=CPU if no NPU/GPU)
OV_MODEL_PATH=./models/phi-4-mini-openvino
OV_DEVICE=AUTO

# Redis / Background Tasks
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
```

## 🏁 Getting Started

### 1. Initialize the Backend

Navigate to the backend directory, install dependencies, and seed the default database project:

```bash
cd services/

# Install dependencies using uv
uv sync

# Seed the database with the default workspace
uv run python seed_project.py

# Start the FastAPI server
uv run uvicorn helios.main:app --host 127.0.0.1 --port 8000 --reload
```

*Note: On first startup, HELIOS may take ~1-2 minutes to load local AI models (like OpenVINO LLMs) into memory.*

### 2. Start the Frontend UI

In a separate terminal window, start the React frontend:

```bash
cd apps/web/

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```

The application will be available at `http://localhost:3000` (or `http://localhost:5173` depending on your Vite config).

### 3. Start the Background Workers (Optional for live scanning)

If you are running live recon tools, you will need a running Redis instance and a Celery worker:
```bash
cd services/
uv run celery -A helios.core.tasks worker --loglevel=info
```

## 📚 Project Structure

*   `apps/web/`: React frontend UI.
*   `apps/desktop/`: Tauri desktop wrapper.
*   `services/helios/`: Main Python backend application.
    *   `api/v1/`: REST API endpoints.
    *   `core/`: Core business logic (Recon parsers, Chat engine, Malware analysis).
    *   `plugins/`: Wrappers for external security tools (Amass, Masscan, etc.).
    *   `models/`: SQLAlchemy ORM database models.

## 🔒 Security & Privacy

HELIOS operates fully offline. Your source code, findings, and target infrastructures are never sent to external third-party cloud APIs. All AI interactions, embeddings, and telemetry are processed locally on your hardware.
