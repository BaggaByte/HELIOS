# PROJECT HELIOS — Detailed Technical Blueprint & Tech Stack

## Document Version: 1.0.0
## Date: 2026-08-01
## Classification: Internal Architecture Document

---

# 1. EXECUTIVE SUMMARY

PROJECT HELIOS is a local-first, AI-powered offensive security copilot designed for authorized penetration testing, bug bounty programs, CTFs, and internal security assessments. It leverages Intel Core Ultra 5 125H with Intel AI Boost NPU via OpenVINO, running Phi-4 Mini INT4 for on-device inference with zero telemetry.

**Key Differentiators:**
- Offline-first architecture — no external AI dependencies during operations
- Evidence-first reasoning — every finding traceable to observed data
- Modular plugin architecture — extensible for custom tools and parsers
- Knowledge graph engine — correlates artifacts across the entire attack surface
- Native desktop performance — optimized for Windows 11 with NPU acceleration

---

# 2. SYSTEM ARCHITECTURE

## 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │   Dashboard │ │  Chat UI    │ │ Recon View  │ │ Knowledge Graph Viz │  │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────────┬────────────┘  │
│         │               │               │                   │               │
│  ┌──────┴───────────────┴───────────────┴───────────────────┴────────────┐  │
│  │                    Tauri Desktop Shell (Rust)                         │  │
│  │  • Window Management  • System Tray  • Native Menus  • File Pickers   │  │
│  └─────────────────────────────┬────────────────────────────────────────┘  │
└────────────────────────────────┼──────────────────────────────────────────┘
                                 │ IPC (JSON-RPC over WebSocket)
┌────────────────────────────────┼──────────────────────────────────────────┐
│                      FRONTEND APPLICATION LAYER                            │
│  ┌─────────────────────────────┴────────────────────────────────────────┐  │
│  │                    React 19 + TypeScript + Vite                     │  │
│  │  • TanStack Query (Server State)    • Zustand (Client State)       │  │
│  │  • React Flow (Graph Visualization) • Monaco Editor (Code View)    │  │
│  │  • Mermaid.js (Diagrams)            • AG Grid (Data Tables)        │  │
│  │  • Tailwind CSS + shadcn/ui         • React Virtualized (Lists)   │  │
│  └─────────────────────────────┬────────────────────────────────────────┘  │
│                                │ HTTP/1.1 + WebSocket                       │
└────────────────────────────────┼──────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼──────────────────────────────────────────┐
│                         API GATEWAY LAYER                                  │
│  ┌─────────────────────────────┴────────────────────────────────────────┐  │
│  │                    FastAPI (Python 3.12+)                             │  │
│  │  • REST API Endpoints  • WebSocket Hub  • JWT Auth  • Rate Limiting  │  │
│  │  • Request Validation  • OpenAPI Docs   • CORS      • Middleware     │  │
│  └─────────────────────────────┬────────────────────────────────────────┘  │
└────────────────────────────────┼──────────────────────────────────────────┘
                                 │ Internal Service Bus (Async)
┌────────────────────────────────┼──────────────────────────────────────────┐
│                        CORE SERVICE LAYER                                  │
│                                                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │ Chat Engine  │ │ Recon Intel  │ │ Web Security │ │ Source Code      │  │
│  │ Service      │ │ Service      │ │ Analysis     │ │ Analysis Service │  │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘  │
│  ┌──────┴───────┐ ┌──────┴───────┐ ┌──────┴───────┐ ┌────────┴─────────┐  │
│  │ JS Intel     │ │ Log Intel    │ │ Malware      │ │ Report Generator │  │
│  │ Service      │ │ Service      │ │ Assistant    │ │ Service          │  │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘  │
│  ┌──────┴────────────────┴────────────────┴──────────────────┴─────────┐  │
│  │                    Shared Kernel Services                              │  │
│  │  • Project Memory  • Evidence System  • Knowledge Graph  • Search    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼──────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                  │
│                                                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │   OpenVINO   │ │   SQLite/    │ │   ChromaDB   │ │   Background     │  │
│  │   Runtime    │ │   PostgreSQL │ │   (Vector)   │ │   Task Queue     │  │
│  │   (NPU/GPU)  │ │              │ │              │ │   (Celery/ARQ)   │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘  │
│                                                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │ File Storage │ │ Plugin       │ │ Encryption   │ │   Event Bus      │  │
│  │ (Local FS)   │ │ Registry     │ │ (Fernet/AES) │ │   (Redis/pubsub) │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Architecture Patterns

| Pattern | Application | Rationale |
|---------|-------------|-----------|
| **Modular Monolith** | Core backend structure | Simpler deployment than microservices, easier to reason about, still modular enough for testing. Can split later if needed. |
| **CQRS (Lite)** | Evidence system writes vs reads | Write-optimized for evidence capture, read-optimized for reporting and timeline views. |
| **Event Sourcing (Lite)** | Audit trail, project timeline | Every action is an event; timeline reconstruction is trivial. |
| **Plugin Architecture** | Tool parsers, AI modules | Hot-swappable parsers for security tools without core redeployment. |
| **Repository Pattern** | All data access | Testable, swappable storage backends (SQLite <-> PostgreSQL). |

---

# 3. TECHNOLOGY STACK & JUSTIFICATION

## 3.1 Desktop Shell

| Technology | Version | Role | Justification |
|------------|---------|------|---------------|
| **Tauri v2** | ^2.0 | Desktop application shell | Rust-based, <600KB overhead (vs 100MB+ Electron), native Windows APIs, WebView2, secure IPC, code signing support, system tray, auto-updater. Critical for local-first security tool where bundle size and memory matter on Intel Core Ultra 5 125H. |
| **Rust** | 1.80+ | Tauri backend commands | Memory safety, zero-cost abstractions, direct Windows API access for file system watchers, native encryption hooks. |

## 3.2 Frontend

| Technology | Version | Role | Justification |
|------------|---------|------|---------------|
| **React** | 19.x | UI framework | Concurrent features, Server Components (where applicable), massive ecosystem, security community familiarity. |
| **TypeScript** | 5.5+ | Type safety | Eliminates entire classes of bugs in a security tool where correctness matters. Self-documenting interfaces. |
| **Vite** | 5.x | Build tool | Instant HMR, optimized production builds, native ESM, plugin ecosystem. |
| **Tailwind CSS** | 3.4+ | Styling | Utility-first, dark theme trivial to implement, no runtime CSS-in-JS overhead, consistent design system. |
| **shadcn/ui** | latest | Component library | Copy-paste components (not a dependency), fully customizable, Radix UI primitives (accessibility), perfect for security tools requiring complex data tables, dialogs, forms. |
| **TanStack Query** | 5.x | Server state management | Caching, background refetching, optimistic updates, WebSocket integration for real-time recon updates. |
| **Zustand** | 4.x | Client state management | Minimal boilerplate, TypeScript-native, no provider hell, perfect for UI state (sidebar, theme, layout). |
| **React Flow** | 12.x | Knowledge graph visualization | Purpose-built for node-based graphs, customizable nodes/edges, performant with large graphs, MIT license. |
| **Monaco Editor** | latest | Code viewing | Same engine as VS Code, syntax highlighting for 15+ languages, diff viewer, minimap — essential for source code and log analysis. |
| **AG Grid** | 31.x | Data tables | Best-in-class grid for large datasets (10k+ hosts, findings), grouping, filtering, export — critical for recon output tables. |
| **Mermaid.js** | 10.x | Diagram rendering | Native markdown diagram support in chat, architecture visualization in reports. |
| **React Markdown** | 9.x | Markdown rendering | Secure by default (no raw HTML), plugin ecosystem, perfect for AI chat responses. |

## 3.3 Backend

| Technology | Version | Role | Justification |
|------------|---------|------|---------------|
| **Python** | 3.12+ | Primary backend language | Dominant in security/AI, massive library ecosystem (scapy, yara-python, lief), OpenVINO first-class support. |
| **FastAPI** | 0.111+ | Web framework | Async-native, automatic OpenAPI docs, WebSocket support, dependency injection, Pydantic validation — ideal for real-time security tool UI. |
| **Pydantic v2** | 2.x | Data validation | 5-50x faster than v1, strict mode for security inputs, JSON Schema generation for frontend types. |
| **SQLAlchemy 2.0** | 2.x | ORM | Async support, type-annotated, query composition, compatible with SQLite and PostgreSQL. |
| **Alembic** | 1.13+ | Database migrations | Industry standard for SQLAlchemy, supports branching migrations for plugin schemas. |
| **Celery** | 5.4+ | Background task queue | Mature, supports Redis/RabbitMQ, task prioritization, rate limiting, retry logic — perfect for long-running recon tasks and AI inference. |
| **OpenVINO** | 2024.3+ | AI inference runtime | Intel-optimized, NPU support for Core Ultra 5 125H, INT4 quantization, model caching, asynchronous inference. |
| **Optimum Intel** | latest | HuggingFace -> OpenVINO | Seamless conversion of Phi-4 Mini to OpenVINO IR format with INT4 weight compression. |
| **ChromaDB** | 0.5+ | Vector database | Local-first, no external server needed, good enough for project-scale RAG (thousands of documents), easy backup. |
| **SentenceTransformers** | 3.x | Embeddings | Generate local embeddings for RAG without API calls, supports CPU/NPU via OpenVINO backend. |
| **Redis** | 7.x | Cache + Pub/Sub | Celery broker, WebSocket broadcast backend, session cache, rate limiting store. |
| **Cryptography** | 42.x | Encryption | Fernet (AES-128-CBC + HMAC) for project data at rest, Argon2 for key derivation. |
| **YARA-Python** | 4.5+ | Malware signature scanning | Industry standard for malware classification, rule-based detection. |
| **LIEF** | 0.14+ | Binary format parsing | ELF/PE/Mach-O metadata extraction, no external dependencies. |

## 3.4 AI / ML Stack

| Component | Specification | Justification |
|-----------|-------------|---------------|
| **Primary LLM** | Phi-4 Mini INT4 (OpenVINO IR) | 3.8B params, optimized for Intel NPU, reasoning capabilities comparable to larger models for security analysis tasks, fits in ~2GB RAM with INT4. |
| **Embedding Model** | all-MiniLM-L6-v2 (OpenVINO) | 384-dim embeddings, fast on CPU/NPU, sufficient for project document retrieval. |
| **Inference Backend** | OpenVINO Runtime + NPU Plugin | Direct Intel AI Boost NPU utilization on Core Ultra 5 125H, ~10x more efficient than CPU for LLM inference. |
| **RAG Framework** | Custom (ChromaDB + SentenceTransformers + Prompt Engineering) | No external dependencies, full local control, evidence citations built into retrieval pipeline. |
| **Context Window** | 128K tokens | Large enough for entire log files, multi-file source code analysis, long recon outputs. |
| **Streaming** | Server-Sent Events (SSE) via FastAPI | Real-time token streaming to UI for chat responses, critical for perceived performance. |

## 3.5 DevOps & Tooling

| Technology | Role | Justification |
|------------|------|---------------|
| **uv** | Python package manager | 10-100x faster than pip, lockfile support, reproducible builds. |
| **Ruff** | Python linting/formatting | Unified tool replacing flake8/black/isort, 10-100x faster. |
| **Pytest** | Testing | Async support, fixtures, coverage, security-focused testing patterns. |
| **GitHub Actions** | CI/CD | Free for open source, Windows runner support for OpenVINO testing. |
| **PyInstaller** | Python backend bundling | Bundle FastAPI + OpenVINO into single executable for Tauri integration. |
| **NSIS / WiX** | Windows installer | Professional installer creation for Windows 11 distribution. |


---

# 4. FOLDER STRUCTURE

```
helios/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
│
├── apps/
│   ├── desktop/                          # Tauri Desktop Applicationl
│   │   ├── src/
│   │   │   ├── main.rs                   # Tauri entry point, command handlers
│   │   │   ├── tray.rs                   # System tray implementation
│   │   │   ├── fs_watcher.rs             # File system event watching
│   │   │   ├── encryption.rs             # Native encryption helpers
│   │   │   └── lib.rs
│   │   ├── Cargo.toml
│   │   ├── tauri.conf.json
│   │   └── icons/
│   │
│   └── web/                              # React Frontend
│       ├── src/
│       │   ├── main.tsx                  # Entry point
│       │   ├── App.tsx                   # Root component, routing
│       │   ├── index.css                 # Tailwind + global styles
│       │   │
│       │   ├── components/             # Reusable UI components
│       │   │   ├── ui/                   # shadcn/ui components
│       │   │   ├── chat/
│       │   │   │   ├── ChatPanel.tsx
│       │   │   │   ├── MessageBubble.tsx
│       │   │   │   ├── CodeBlock.tsx
│       │   │   │   ├── FileUpload.tsx
│       │   │   │   └── StreamingText.tsx
│       │   │   ├── recon/
│       │   │   │   ├── HostTable.tsx
│       │   │   │   ├── PortMatrix.tsx
│       │   │   │   ├── ServiceCard.tsx
│       │   │   │   └── ToolOutputParser.tsx
│       │   │   ├── graph/
│       │   │   │   ├── KnowledgeGraph.tsx
│       │   │   │   ├── NodeTypes.tsx
│       │   │   │   └── EdgeTypes.tsx
│       │   │   ├── evidence/
│       │   │   │   ├── EvidenceCard.tsx
│       │   │   │   ├── ConfidenceBadge.tsx
│       │   │   │   └── Timeline.tsx
│       │   │   ├── code/
│       │   │   │   ├── CodeViewer.tsx
│       │   │   │   ├── DependencyGraph.tsx
│       │   │   │   └── SecretHighlight.tsx
│       │   │   └── layout/
│       │   │       ├── Sidebar.tsx
│       │   │       ├── TopBar.tsx
│       │   │       ├── SplitPane.tsx
│       │   │       └── TabbedPanel.tsx
│       │   │
│       │   ├── hooks/                    # Custom React hooks
│       │   │   ├── useChat.ts
│       │   │   ├── useProjectMemory.ts
│       │   │   ├── useWebSocket.ts
│       │   │   ├── useKeyboardShortcuts.ts
│       │   │   └── useDragAndDrop.ts
│       │   │
│       │   ├── stores/                   # Zustand stores
│       │   │   ├── uiStore.ts
│       │   │   ├── projectStore.ts
│       │   │   ├── chatStore.ts
│       │   │   └── evidenceStore.ts
│       │   │
│       │   ├── services/                 # API clients
│       │   │   ├── apiClient.ts          # Axios/fetch wrapper
│       │   │   ├── chatService.ts
│       │   │   ├── reconService.ts
│       │   │   └── fileService.ts
│       │   │
│       │   ├── types/                    # TypeScript interfaces
│       │   │   ├── api.ts
│       │   │   ├── models.ts
│       │   │   └── enums.ts
│       │   │
│       │   ├── utils/                    # Frontend utilities
│       │   │   ├── formatters.ts
│       │   │   ├── parsers.ts
│       │   │   └── validators.ts
│       │   │
│       │   └── features/                 # Feature modules (colocation)
│       │       ├── dashboard/
│       │       ├── chat/
│       │       ├── recon/
│       │       ├── web-security/
│       │       ├── source-code/
│       │       ├── js-intel/
│       │       ├── logs/
│       │       ├── malware/
│       │       ├── knowledge-graph/
│       │       ├── evidence/
│       │       ├── reports/
│       │       └── settings/
│       │
│       ├── index.html
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── tailwind.config.js
│       └── package.json
│
├── services/                             # Python Backend
│   ├── helios/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI application factory
│   │   ├── config.py                     # Pydantic Settings (env vars)
│   │   ├── dependencies.py             # FastAPI DI container
│   │   ├── lifespan.py                 # Startup/shutdown events
│   │   │
│   │   ├── api/                          # API Layer
│   │   │   ├── __init__.py
│   │   │   ├── router.py                 # Main API router aggregator
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat.py               # Chat endpoints + WebSocket
│   │   │   │   ├── projects.py           # CRUD + context
│   │   │   │   ├── recon.py              # Recon ingestion + analysis
│   │   │   │   ├── web_security.py       # HTTP analysis endpoints
│   │   │   │   ├── source_code.py        # Code upload + analysis
│   │   │   │   ├── js_intel.py           # JavaScript extraction
│   │   │   │   ├── logs.py               # Log ingestion + timeline
│   │   │   │   ├── malware.py            # Malware triage endpoints
│   │   │   │   ├── evidence.py           # Evidence CRUD
│   │   │   │   ├── knowledge_graph.py    # Graph query + mutation
│   │   │   │   ├── reports.py            # Report generation
│   │   │   │   ├── files.py              # File upload/download
│   │   │   │   ├── search.py             # Global search
│   │   │   │   └── system.py             # Health, settings, status
│   │   │
│   │   ├── core/                         # Domain Logic (Services)
│   │   │   ├── __init__.py
│   │   │   ├── chat/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── engine.py             # Chat orchestration
│   │   │   │   ├── memory.py             # Conversation memory management
│   │   │   │   ├── rag.py                # Retrieval-augmented generation
│   │   │   │   └── prompts.py            # System prompts + templates
│   │   │   │
│   │   │   ├── recon/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ingestor.py           # Generic tool output ingestor
│   │   │   │   ├── parsers/              # Tool-specific parsers
│   │   │   │   │   ├── nmap.py
│   │   │   │   │   ├── masscan.py
│   │   │   │   │   ├── rustscan.py
│   │   │   │   │   ├── httpx.py
│   │   │   │   │   ├── amass.py
│   │   │   │   │   ├── subfinder.py
│   │   │   │   │   ├── dnsx.py
│   │   │   │   │   ├── naabu.py
│   │   │   │   │   ├── katana.py
│   │   │   │   │   ├── gau.py
│   │   │   │   │   ├── ffuf.py
│   │   │   │   │   ├── gobuster.py
│   │   │   │   │   ├── dirsearch.py
│   │   │   │   │   ├── whatweb.py
│   │   │   │   │   ├── nikto.py
│   │   │   │   │   └── nuclei.py
│   │   │   │   ├── analyzer.py           # Attack surface analysis
│   │   │   │   └── prioritizer.py        # Risk-based prioritization
│   │   │   │
│   │   │   ├── web_security/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── burp_parser.py
│   │   │   │   ├── http_analyzer.py      # Request/response analysis
│   │   │   │   ├── jwt_analyzer.py
│   │   │   │   ├── oauth_analyzer.py
│   │   │   │   ├── saml_analyzer.py
│   │   │   │   ├── graphql_analyzer.py
│   │   │   │   ├── openapi_analyzer.py
│   │   │   │   └── detector.py           # Pattern-based detection
│   │   │   │
│   │   │   ├── source_code/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── loader.py             # Multi-language AST loading
│   │   │   │   ├── analyzers/
│   │   │   │   │   ├── python_analyzer.py
│   │   │   │   │   ├── go_analyzer.py
│   │   │   │   │   ├── rust_analyzer.py
│   │   │   │   │   ├── java_analyzer.py
│   │   │   │   │   ├── csharp_analyzer.py
│   │   │   │   │   ├── c_analyzer.py
│   │   │   │   │   ├── cpp_analyzer.py
│   │   │   │   │   ├── js_analyzer.py
│   │   │   │   │   ├── ts_analyzer.py
│   │   │   │   │   ├── php_analyzer.py
│   │   │   │   │   ├── ruby_analyzer.py
│   │   │   │   │   └── node_analyzer.py
│   │   │   │   ├── dependency_graph.py
│   │   │   │   ├── secret_detector.py
│   │   │   │   └── pattern_matcher.py
│   │   │   │
│   │   │   ├── js_intel/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── extractor.py          # JS static analysis
│   │   │   │   ├── endpoint_finder.py
│   │   │   │   ├── token_extractor.py
│   │   │   │   └── deobfuscator.py       # Basic deobfuscation
│   │   │   │
│   │   │   ├── logs/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── parsers/
│   │   │   │   │   ├── suricata.py
│   │   │   │   │   ├── zeek.py
│   │   │   │   │   ├── apache.py
│   │   │   │   │   ├── nginx.py
│   │   │   │   │   ├── windows_event.py
│   │   │   │   │   ├── sysmon.py
│   │   │   │   │   ├── linux_auth.py
│   │   │   │   │   ├── docker.py
│   │   │   │   │   └── kubernetes.py
│   │   │   │   ├── timeline_builder.py
│   │   │   │   ├── ioc_extractor.py
│   │   │   │   └── mitre_mapper.py
│   │   │   │
│   │   │   ├── malware/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── triage.py
│   │   │   │   ├── static_analyzer.py
│   │   │   │   ├── behavior_analyzer.py
│   │   │   │   ├── yara_scanner.py
│   │   │   │   └── pe_analyzer.py
│   │   │   │
│   │   │   ├── reports/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── generator.py
│   │   │   │   ├── templates/
│   │   │   │   │   ├── executive_summary.md
│   │   │   │   │   ├── technical_findings.md
│   │   │   │   │   └── appendix.md
│   │   │   │   ├── formatters/
│   │   │   │   │   ├── markdown.py
│   │   │   │   │   ├── pdf.py
│   │   │   │   │   └── docx.py
│   │   │   │   └── risk_calculator.py
│   │   │   │
│   │   │   ├── knowledge_graph/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── builder.py            # Graph construction
│   │   │   │   ├── query_engine.py       # GraphQL-like queries
│   │   │   │   ├── embeddings.py         # Node embeddings
│   │   │   │   └── models.py             # Node/Edge domain models
│   │   │   │
│   │   │   ├── evidence/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manager.py            # Evidence lifecycle
│   │   │   │   ├── validator.py          # Evidence integrity
│   │   │   │   └── chain_of_custody.py   # Audit trail
│   │   │   │
│   │   │   └── project_memory/
│   │   │       ├── __init__.py
│   │   │       ├── store.py              # Contextual memory
│   │   │       ├── retriever.py          # Semantic search over memory
│   │   │       └── deduplicator.py       # Avoid duplicate recommendations
│   │   │
│   │   ├── models/                       # Database Models (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   # Base class, mixins
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── target.py
│   │   │   ├── host.py
│   │   │   ├── service.py
│   │   │   ├── finding.py
│   │   │   ├── evidence.py
│   │   │   ├── note.py
│   │   │   ├── file.py
│   │   │   ├── chat_message.py
│   │   │   ├── knowledge_node.py
│   │   │   ├── knowledge_edge.py
│   │   │   └── task.py
│   │   │
│   │   ├── schemas/                      # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py                 # Pagination, response wrappers
│   │   │   ├── chat.py
│   │   │   ├── project.py
│   │   │   ├── recon.py
│   │   │   ├── evidence.py
│   │   │   ├── knowledge_graph.py
│   │   │   └── report.py
│   │   │
│   │   ├── infrastructure/               # Infrastructure Concerns
│   │   │   ├── __init__.py
│   │   │   ├── database.py               # SQLAlchemy engine/session
│   │   │   ├── vector_db.py              # ChromaDB client
│   │   │   ├── cache.py                  # Redis cache wrapper
│   │   │   ├── storage.py                # File system abstraction
│   │   │   ├── encryption.py             # At-rest encryption
│   │   │   ├── openvino_runtime.py       # NPU/GPU inference manager
│   │   │   ├── celery_app.py             # Celery configuration
│   │   │   ├── event_bus.py              # Pub/sub for real-time updates
│   │   │   └── plugin_registry.py        # Dynamic plugin loading
│   │   │
│   │   ├── plugins/                      # Plugin System
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   # Plugin ABC
│   │   │   ├── loader.py                 # Dynamic import
│   │   │   └── builtin/                  # Built-in plugins
│   │   │       ├── nmap_enhancer/
│   │   │       ├── nuclei_enhancer/
│   │   │       └── custom_tool/
│   │   │
│   │   └── utils/                        # Shared Utilities
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       ├── sanitizers.py             # File upload sanitization
│   │       ├── hashers.py
│   │       ├── mitre_attack.py           # MITRE ATT&CK reference data
│   │       └── cvss_calculator.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── e2e/
│   │   └── conftest.py
│   │
│   ├── alembic/                          # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile
│
├── models/                               # AI Model Storage
│   ├── phi-4-mini-int4/                  # OpenVINO IR format
│   ├── embeddings/
│   └── yara-rules/
│
├── docs/                                 # Documentation
│   ├── architecture/
│   ├── api/
│   ├── deployment/
│   └── user-guide/
│
├── scripts/                              # Automation scripts
│   ├── setup-openvino.ps1
│   ├── build-windows.ps1
│   └── install-yara-rules.sh
│
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```


---

# 5. DATABASE SCHEMA

## 5.1 Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │   Project   │       │   Target    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │◄──────┤ id (PK)     │◄──────┤ id (PK)     │
│ username    │       │ name        │       │ project_id  │
│ password_hash│      │ description │       │ type        │
│ role        │       │ scope       │       │ value       │
│ created_at  │       │ status      │       │ notes       │
└─────────────┘       │ created_at  │       │ created_at  │
                      └──────┬──────┘       └─────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │   Host    │  │   Task    │  │   File    │
        ├───────────┤  ├───────────┤  ├───────────┤
        │ id (PK)   │  │ id (PK)   │  │ id (PK)   │
        │ project_id│  │ project_id│  │ project_id│
        │ ip        │  │ title     │  │ filename  │
        │ hostname  │  │ status    │  │ mime_type │
        │ os        │  │ priority  │  │ size      │
        │ notes     │  │ assigned_to│  │ hash      │
        │ created_at│  │ due_date  │  │ encrypted │
        └─────┬─────┘  │ created_at│  │ created_at│
              │        └───────────┘  └───────────┘
        ┌─────▼─────┐
        │  Service  │
        ├───────────┤
        │ id (PK)   │
        │ host_id   │
        │ port      │
        │ protocol  │
        │ name      │
        │ version   │
        │ banner    │
        │ state     │
        └─────┬─────┘
              │
        ┌─────▼─────┐       ┌─────────────┐       ┌─────────────┐
        │  Finding  │◄──────┤  Evidence   │       │    Note     │
        ├───────────┤       ├─────────────┤       ├─────────────┤
        │ id (PK)   │       │ id (PK)     │       │ id (PK)     │
        │ service_id│       │ finding_id  │       │ project_id  │
        │ title     │       │ type        │       │ title       │
        │ severity  │       │ data        │       │ content     │
        │ confidence│       │ file_path   │       │ tags        │
        │ status    │       │ hash        │       │ created_at  │
        │ cvss_score│       │ created_at  │       └─────────────┘
        │ description      └─────────────┘
        │ remediation
        │ cwe_id
        │ created_at
        └───────────┘

┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│KnowledgeNode│       │KnowledgeEdge│       │ChatMessage  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │◄──────┤ id (PK)     │       │ id (PK)     │
│ project_id  │       │ source_id   │       │ project_id  │
│ type        │       │ target_id   │       │ role        │
│ label       │       │ relation    │       │ content     │
│ properties  │       │ properties  │       │ metadata    │
│ embedding   │       │ created_at  │       │ tokens_used │
│ created_at  │       └─────────────┘       │ created_at  │
└─────────────┘                             └─────────────┘
```

## 5.2 Detailed Schema Definitions

### Table: `users`
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,  -- Argon2id
    role            VARCHAR(20) NOT NULL DEFAULT 'analyst', -- admin, analyst, viewer
    preferences     JSONB DEFAULT '{}',
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `projects`
```sql
CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    scope           TEXT NOT NULL,  -- Explicit in-scope definition
    out_of_scope    TEXT,           -- Explicit out-of-scope definition
    status          VARCHAR(20) DEFAULT 'active', -- active, paused, completed, archived
    encryption_key_id VARCHAR(100),  -- Reference to key in keystore
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `targets`
```sql
CREATE TABLE targets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type            VARCHAR(20) NOT NULL, -- domain, ip_range, url, cidr, wildcard
    value           VARCHAR(500) NOT NULL,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_targets_project ON targets(project_id);
```

### Table: `hosts`
```sql
CREATE TABLE hosts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ip              INET NOT NULL,
    hostname        VARCHAR(255),
    os              VARCHAR(100),
    os_version      VARCHAR(100),
    mac_address     MACADDR,
    notes           TEXT,
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, ip)
);
CREATE INDEX idx_hosts_project ON hosts(project_id);
CREATE INDEX idx_hosts_ip ON hosts(ip);
```

### Table: `services`
```sql
CREATE TABLE services (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    host_id         UUID NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
    port            INTEGER NOT NULL CHECK (port > 0 AND port <= 65535),
    protocol        VARCHAR(10) NOT NULL DEFAULT 'tcp', -- tcp, udp, sctp
    name            VARCHAR(100),  -- nmap service name
    version         VARCHAR(255),
    banner          TEXT,
    state           VARCHAR(20) DEFAULT 'open', -- open, closed, filtered
    cpe             VARCHAR(255),  -- CPE identifier
    metadata        JSONB DEFAULT '{}',  -- tool-specific extra data
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(host_id, port, protocol)
);
CREATE INDEX idx_services_host ON services(host_id);
CREATE INDEX idx_services_port ON services(port);
```

### Table: `findings`
```sql
CREATE TABLE findings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    service_id      UUID REFERENCES services(id) ON DELETE SET NULL,
    title           VARCHAR(500) NOT NULL,
    description     TEXT NOT NULL,
    severity        VARCHAR(20) NOT NULL, -- critical, high, medium, low, info
    confidence      VARCHAR(20) NOT NULL, -- high, medium, low
    status          VARCHAR(20) DEFAULT 'observed', -- observed, needs_verification, verified, false_positive, closed
    cvss_score      NUMERIC(3,1),
    cvss_vector     VARCHAR(100),
    cwe_id          VARCHAR(20),
    capec_id        VARCHAR(20),
    remediation     TEXT,
    impact          TEXT,
    references      JSONB DEFAULT '[]',
    ai_analysis     TEXT,  -- AI-generated analysis (clearly labeled)
    ai_confidence   NUMERIC(3,2),  -- AI's confidence in its own analysis
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_findings_project ON findings(project_id);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_status ON findings(status);
```

### Table: `evidence`
```sql
CREATE TABLE evidence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id      UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    type            VARCHAR(30) NOT NULL, -- screenshot, log_excerpt, request_response, file_hash, command_output, network_capture
    description     TEXT,
    file_path       VARCHAR(1000),  -- Relative path in encrypted storage
    file_hash       VARCHAR(64),  -- SHA-256 of original file
    data            TEXT,  -- Inline evidence (for small text evidence)
    metadata        JSONB DEFAULT '{}',  -- Source tool, command used, timestamp
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_evidence_finding ON evidence(finding_id);
```

### Table: `knowledge_nodes`
```sql
CREATE TABLE knowledge_nodes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type            VARCHAR(30) NOT NULL, -- domain, host, user, technology, certificate, service, evidence, file, note, finding
    label           VARCHAR(255) NOT NULL,
    properties      JSONB DEFAULT '{}',
    embedding       VECTOR(384),  -- pgvector extension for semantic search
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_knodes_project ON knowledge_nodes(project_id);
CREATE INDEX idx_knodes_type ON knowledge_nodes(type);
CREATE INDEX idx_knodes_embedding ON knowledge_nodes USING ivfflat (embedding vector_cosine_ops);
```

### Table: `knowledge_edges`
```sql
CREATE TABLE knowledge_edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_id       UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_id       UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relation        VARCHAR(50) NOT NULL, -- resolves_to, runs_on, uses, contains, authenticates_to, etc.
    properties      JSONB DEFAULT '{}',
    confidence      NUMERIC(3,2) DEFAULT 1.0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id, target_id, relation)
);
CREATE INDEX idx_kedges_project ON knowledge_edges(project_id);
CREATE INDEX idx_kedges_source ON knowledge_edges(source_id);
CREATE INDEX idx_kedges_target ON knowledge_edges(target_id);
```

### Table: `chat_messages`
```sql
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL, -- system, user, assistant, tool
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',  -- model used, tokens, reasoning steps, citations
    parent_id       UUID REFERENCES chat_messages(id),  -- For branching conversations
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_chat_project ON chat_messages(project_id);
CREATE INDEX idx_chat_created ON chat_messages(created_at);
```

### Table: `files`
```sql
CREATE TABLE files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename        VARCHAR(255) NOT NULL,
    original_name   VARCHAR(255) NOT NULL,
    mime_type       VARCHAR(100),
    size_bytes      BIGINT,
    sha256          VARCHAR(64) NOT NULL,
    storage_path    VARCHAR(1000) NOT NULL,
    encrypted       BOOLEAN DEFAULT TRUE,
    metadata        JSONB DEFAULT '{}',  -- parsed preview, structure
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_files_project ON files(project_id);
CREATE INDEX idx_files_sha256 ON files(sha256);
```

### Table: `tasks`
```sql
CREATE TABLE tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    status          VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, blocked
    priority        VARCHAR(10) DEFAULT 'medium', -- low, medium, high, critical
    assigned_to     UUID REFERENCES users(id),
    due_date        TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
```

### Table: `events` (Event Sourcing / Audit)
```sql
CREATE TABLE events (
    id              BIGSERIAL PRIMARY KEY,
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    actor_id        UUID REFERENCES users(id),
    action          VARCHAR(50) NOT NULL, -- finding_created, evidence_added, tool_output_ingested
    entity_type     VARCHAR(50) NOT NULL,
    entity_id       UUID,
    payload         JSONB NOT NULL,
    ip_address      INET,
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_events_project ON events(project_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
```


---

# 6. BACKEND API DESIGN

## 6.1 REST API Endpoints

### Authentication & System
```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/system/health
GET    /api/v1/system/status          # OpenVINO, NPU, memory, disk
GET    /api/v1/system/settings
PUT    /api/v1/system/settings
```

### Projects & Context
```
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{id}
PUT    /api/v1/projects/{id}
DELETE /api/v1/projects/{id}
GET    /api/v1/projects/{id}/context   # Full project memory snapshot
POST   /api/v1/projects/{id}/scope     # Update scope
```

### Chat (REST fallback + WebSocket primary)
```
GET    /api/v1/projects/{id}/chat/messages
POST   /api/v1/projects/{id}/chat/messages        # Non-streaming
DELETE /api/v1/projects/{id}/chat/messages/{msg_id}
POST   /api/v1/projects/{id}/chat/upload           # Image/file for context
WS     /ws/v1/projects/{id}/chat                   # Real-time streaming chat
```

### Reconnaissance
```
POST   /api/v1/projects/{id}/recon/ingest          # Generic tool output
POST   /api/v1/projects/{id}/recon/nmap             # Nmap-specific
POST   /api/v1/projects/{id}/recon/masscan
POST   /api/v1/projects/{id}/recon/httpx
POST   /api/v1/projects/{id}/recon/subfinder
# ... (one endpoint per supported tool)
GET    /api/v1/projects/{id}/recon/hosts
GET    /api/v1/projects/{id}/recon/services
GET    /api/v1/projects/{id}/recon/attack-surface  # AI-analyzed summary
GET    /api/v1/projects/{id}/recon/priorities      # Risk-ranked findings
```

### Web Security
```
POST   /api/v1/projects/{id}/web-security/burp      # Import Burp Suite export
POST   /api/v1/projects/{id}/web-security/http     # Analyze raw HTTP
POST   /api/v1/projects/{id}/web-security/jwt      # Decode + analyze JWT
POST   /api/v1/projects/{id}/web-security/oauth    # OAuth flow analysis
POST   /api/v1/projects/{id}/web-security/saml      # SAML response analysis
POST   /api/v1/projects/{id}/web-security/graphql   # GraphQL introspection
POST   /api/v1/projects/{id}/web-security/openapi    # OpenAPI security review
```

### Source Code
```
POST   /api/v1/projects/{id}/source-code/upload      # ZIP/repo upload
GET    /api/v1/projects/{id}/source-code/files        # File tree
GET    /api/v1/projects/{id}/source-code/files/{path} # File content
GET    /api/v1/projects/{id}/source-code/analysis     # Full analysis results
GET    /api/v1/projects/{id}/source-code/dependencies # Dependency graph
GET    /api/v1/projects/{id}/source-code/secrets      # Detected secrets
```

### JavaScript Intelligence
```
POST   /api/v1/projects/{id}/js-intel/analyze       # JS file or URL
GET    /api/v1/projects/{id}/js-intel/endpoints      # Discovered endpoints
GET    /api/v1/projects/{id}/js-intel/tokens         # Extracted tokens
GET    /api/v1/projects/{id}/js-intel/routes          # Hidden routes
```

### Log Intelligence
```
POST   /api/v1/projects/{id}/logs/ingest            # Generic log ingest
POST   /api/v1/projects/{id}/logs/suricata
POST   /api/v1/projects/{id}/logs/zeek
POST   /api/v1/projects/{id}/logs/windows
# ...
GET    /api/v1/projects/{id}/logs/timeline           # Attack timeline
GET    /api/v1/projects/{id}/logs/iocs               # Extracted IOCs
GET    /api/v1/projects/{id}/logs/mitre              # MITRE ATT&CK mapping
GET    /api/v1/projects/{id}/logs/summary            # AI-generated summary
```

### Malware Triage
```
POST   /api/v1/projects/{id}/malware/upload         # Sample upload
GET    /api/v1/projects/{id}/malware/{id}/analysis # Static analysis
GET    /api/v1/projects/{id}/malware/{id}/yara      # YARA matches
GET    /api/v1/projects/{id}/malware/{id}/behavior # Behavior indicators
GET    /api/v1/projects/{id}/malware/{id}/strings   # Extracted strings
```

### Knowledge Graph
```
GET    /api/v1/projects/{id}/graph/nodes            # List nodes
POST   /api/v1/projects/{id}/graph/nodes            # Create node
GET    /api/v1/projects/{id}/graph/edges            # List edges
POST   /api/v1/projects/{id}/graph/edges            # Create edge
GET    /api/v1/projects/{id}/graph/query            # Complex graph query
GET    /api/v1/projects/{id}/graph/neighbors/{node_id} # Node neighborhood
POST   /api/v1/projects/{id}/graph/rebuild          # Rebuild from project data
```

### Evidence System
```
GET    /api/v1/projects/{id}/evidence
POST   /api/v1/projects/{id}/evidence               # Create evidence
GET    /api/v1/projects/{id}/evidence/{id}
PUT    /api/v1/projects/{id}/evidence/{id}
DELETE /api/v1/projects/{id}/evidence/{id}
POST   /api/v1/projects/{id}/evidence/{id}/attach  # Attach file
```

### Findings
```
GET    /api/v1/projects/{id}/findings
POST   /api/v1/projects/{id}/findings
GET    /api/v1/projects/{id}/findings/{id}
PUT    /api/v1/projects/{id}/findings/{id}
DELETE /api/v1/projects/{id}/findings/{id}
POST   /api/v1/projects/{id}/findings/{id}/verify   # Mark verified
```

### Reports
```
POST   /api/v1/projects/{id}/reports/generate        # Trigger generation
GET    /api/v1/projects/{id}/reports                 # List reports
GET    /api/v1/projects/{id}/reports/{id}           # Download (markdown/pdf/docx)
DELETE /api/v1/projects/{id}/reports/{id}
```

### Files & Uploads
```
POST   /api/v1/projects/{id}/files                   # Upload file
GET    /api/v1/projects/{id}/files
GET    /api/v1/projects/{id}/files/{id}/download
DELETE /api/v1/projects/{id}/files/{id}
```

### Search
```
GET    /api/v1/projects/{id}/search?q={query}&type={type}  # Global project search
POST   /api/v1/projects/{id}/search/semantic            # Vector semantic search
```

## 6.2 WebSocket Events

```
Connection: wss://localhost:8443/ws/v1/projects/{project_id}

Client -> Server:
  chat.message          { content, attachments[], streaming: true }
  chat.stop             { message_id }
  recon.ingest          { tool, raw_output, metadata }
  file.upload           { filename, chunk, index, total }

Server -> Client:
  chat.token            { message_id, token, done }
  chat.citation         { message_id, evidence_id, snippet }
  chat.error            { message_id, error, code }
  recon.progress        { task_id, tool, percent, status }
  recon.complete        { task_id, summary, new_findings_count }
  graph.update          { nodes_added[], edges_added[] }
  evidence.new          { evidence_id, finding_id, preview }
  system.status         { cpu, memory, npu_util, queue_length }
  notification          { type, title, message, severity }
```

## 6.3 API Design Principles

1. **Project-Scoped**: All endpoints include {project_id} — no global data leakage between engagements.
2. **Streaming First**: Chat and long-running analysis use WebSocket streaming; REST is for CRUD.
3. **Idempotency**: All mutation endpoints accept Idempotency-Key header for safe retries.
4. **Pagination**: All list endpoints use cursor-based pagination (limit + after_id).
5. **Content Negotiation**: Reports support Accept: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, text/markdown.
6. **Validation**: Strict Pydantic v2 validation with extra='forbid' on all input schemas.

---

# 7. FRONTEND WIREFRAMES & UI SPECIFICATION

## 7.1 Design System

**Theme**: Professional dark theme optimized for long sessions.

```css
/* Core Tokens */
--bg-primary:       #0d1117;    /* Main background */
--bg-secondary:     #161b22;    /* Panels, cards */
--bg-tertiary:      #21262d;    /* Elevated surfaces */
--bg-hover:         #30363d;    /* Interactive hover */
--border-default:   #30363d;
--border-active:    #58a6ff;

/* Semantic Colors */
--severity-critical: #f85149;
--severity-high:     #fa7b3c;
--severity-medium:   #d29922;
--severity-low:      #3fb950;
--severity-info:     #58a6ff;

--confidence-high:   #3fb950;
--confidence-medium: #d29922;
--confidence-low:    #8b949e;

/* Typography */
--font-mono:  'JetBrains Mono', 'Fira Code', monospace;
--font-sans:  'Inter', system-ui, sans-serif;
--font-size-base: 14px;
```

## 7.2 Screen Specifications

### Dashboard (Default View)
```
+-----------------------------------------------------------------------------+
|  ≡  HELIOS                                          [Search]  [⚙] [👤]      |
+--------+--------------------------------------------------------------------+
|        |  PROJECT: ACME Corp Penetration Test                    [+ New]  |
| DASH   |  +-------------+ +-------------+ +-------------+ +-------------+   |
| CHAT   |  |   Hosts     | |  Services   | |  Findings   | |   Tasks     |   |
| RECON  |  |    142      | |    387      | |     23      | |     8/12    |   |
| WEB    |  |  ▲ 12%      | |  ▲ 8%       | |  ▲ 3 new    | |  4 pending  |   |
| CODE   |  +-------------+ +-------------+ +-------------+ +-------------+   |
| LOGS   |                                                                      |
| MALWARE|  +------------------------------+  +------------------------------+  |
| GRAPH  |  |      RECENT ACTIVITY         |  |      ATTACK SURFACE        |  |
| EVIDENCE| |  • Nmap scan completed       |  |  [Radar/Spider Chart]        |  |
| REPORTS|  |  • 3 findings auto-generated |  |  Top ports: 80,443,22,3389  |  |
| FILES  |  |  • Burp export imported      |  |  Technologies: ASP.NET, IIS  |  |
|        |  |  • AI analysis: 2 complete   |  |  Risk score: 7.2/10          |  |
|        |  +------------------------------+  +------------------------------+  |
|        |                                                                      |
|        |  +--------------------------------------------------------------+  |
|        |  |              KNOWLEDGE GRAPH PREVIEW                         |  |
|        |  |  [Mini force-directed graph with 20-30 nodes, clickable]   |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
+--------+--------------------------------------------------------------------+
```

### Chat Interface
```
+-----------------------------------------------------------------------------+
|  ≡  HELIOS                                        Project: ACME Corp       |
+--------+--------------------------------------------------------------------+
|        |                                                                      |
|        |  +--------------------------------------------------------------+  |
|        |  | HELIOS                                                       |  |
|        |  | I've analyzed the Nmap output. Here are the key findings:  |  |
|        |  |                                                              |  |
|        |  | 1. **Port 3389 (RDP)** exposed on 3 hosts [Evidence: E-12] |  |
|        |  |    - Risk: High — RDP without NLA on 10.0.1.15            |  |
|        |  |    - Recommendation: Verify if NLA is enforced            |  |
|        |  |                                                              |  |
|        |  | 2. **IIS 10.0** with ASP.NET detected on 10.0.1.20       |  |
|        |  |    - Note: Check for .NET deserialization vulnerabilities   |  |
|        |  |                                                              |  |
|        |  | [View in Graph]  [Add to Findings]  [Export]              |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
|        |  +--------------------------------------------------------------+  |
|        |  | You                                                          |  |
|        |  | Analyze the JavaScript bundle for api endpoints and tokens |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
|        |  +--------------------------------------------------------------+  |
|        |  | HELIOS  [thinking...]                                        |  |
|        |  | Analyzing main.bundle.js...                                 |  |
|        |  | ████████████░░░░░░░░  45%                                   |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
|        +--------------------------------------------------------------------+
|        |  [📎] [📷] [📁]  +------------------------------------+ [➤]  |
|        |                  | Type a message or drop files here... |      |
|        |                  +------------------------------------+      |
+--------+--------------------------------------------------------------------+
```

### Reconnaissance View
```
+-----------------------------------------------------------------------------+
|  ≡  HELIOS                                        [Search]  [⚙] [👤]      |
+--------+--------------------------------------------------------------------+
|        |  RECONNAISSANCE                                      [+ Ingest]  |
|        |  +----------+ +----------+ +----------+ +----------+           |
|        |  |  Hosts   | | Services | |  Tools   | | Timeline |           |
|        |  |  (142)   | |  (387)   | |  (8)     | |          |           |
|        |  +----------+ +----------+ +----------+ +----------+           |
|        |                                                                      |
|        |  +--------------------------------------------------------------+  |
|        |  |  Hosts Table (AG Grid)                                       |  |
|        |  |  +------+-------------+--------------+--------+------------+ |  |
|        |  |  | IP   | Hostname    | OS           | Ports  | Risk       | |  |
|        |  |  +------+-------------+--------------+--------+------------+ |  |
|        |  |  |10.0..| web01.acme| Windows 2022 | 80,443 | ▲ High     | |  |
|        |  |  |10.0..| dc01.acme | Windows 2022 | 53,88..| ▲ Critical | |  |
|        |  |  |10.0..| app01.acme| Ubuntu 22.04 | 22,8080| ▲ Medium   | |  |
|        |  |  +------+-------------+--------------+--------+------------+ |  |
|        |  |  [Filter] [Group by OS] [Export CSV] [AI Analyze Selected] |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
|        |  +------------------------+  +--------------------------------+  |
|        |  |  SERVICE BREAKDOWN     |  |  AI RECOMMENDATIONS            |  |
|        |  |  [Donut Chart]         |  |  • Run nuclei on web services  |  |
|        |  |  HTTP: 45%             |  |  • Check AD misconfigurations  |  |
|        |  |  SMB: 20%              |  |  • Investigate exposed RDP     |  |
|        |  |  RDP: 15%              |  |  • Review IIS configurations   |  |
|        |  |  Other: 20%            |  |                                |  |
|        |  +------------------------+  +--------------------------------+  |
|        |                                                                      |
+--------+--------------------------------------------------------------------+
```

### Knowledge Graph View
```
+-----------------------------------------------------------------------------+
|  ≡  HELIOS                                        [Search]  [⚙] [👤]      |
+--------+--------------------------------------------------------------------+
|        |  KNOWLEDGE GRAPH                                               |
|        |  +--------------------------------------------------------------+  |
|        |  |                                                            |  |
|        |  |         [Domain: acme.com]                                |  |
|        |  |              |                                              |  |
|        |  |      +-------+-------+                                      |  |
|        |  |      v               v                                      |  |
|        |  | [Host: 10.0.1.20] [Host: 10.0.1.15]                        |  |
|        |  |      |                      |                                |  |
|        |  |      v                      v                             |  |
|        |  | [Svc: IIS 10.0]      [Svc: RDP 3389]                       |  |
|        |  |      |                      |                                |  |
|        |  |      v                      v                             |  |
|        |  | [Tech: ASP.NET]      [Finding: RDP-NLA]                   |  |
|        |  |      |                                                 |  |
|        |  |      v                                                 |  |
|        |  | [Evidence: Screenshot]                                   |  |
|        |  |                                                            |  |
|        |  |  [Legend: ■ Domain ■ Host ■ Service ■ Tech ■ Finding]  |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
|        |  [Search nodes...]  [Filter by type ▼]  [Reset view]  [Export PNG] |
|        |                                                                      |
+--------+--------------------------------------------------------------------+
```

### Evidence Detail View
```
+-----------------------------------------------------------------------------+
|  ≡  HELIOS                                        [Search]  [⚙] [👤]      |
+--------+--------------------------------------------------------------------+
|        |  EVIDENCE: E-042 — RDP Exposure on 10.0.1.15                  |
|        |                                                                      |
|        |  +--------------------------------------------------------------+  |
|        |  |  METADATA                                                    |  |
|        |  |  Status:     [Observed ▼]  Confidence: [High ▼]           |  |
|        |  |  Severity:   [High ▼]       Impact:     [Medium ▼]        |  |
|        |  |  CVSS:       7.5 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N)|
|        |  |  CWE:        CWE-287 (Improper Authentication)              |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
|        |  +--------------------------------------------------------------+  |
|        |  |  EVIDENCE ITEMS                                              |  |
|        |  |  +--------+ +----------------------------------------------+ |  |
|        |  |  | [Img]  | | Nmap Output Excerpt:                       | |  |
|        |  |  |        | | PORT     STATE SERVICE VERSION             | |  |
|        |  |  |        | | 3389/tcp open  ms-wbt-server Microsoft RDP   | |  |
|        |  |  |        | | | RDP Negotiation Failure: NLA not required| |  |
|        |  |  +--------+ +----------------------------------------------+ |  |
|        |  |  [+ Add Evidence] [Verify] [Link to Finding]               |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
|        |  +--------------------------------------------------------------+  |
|        |  |  AI ANALYSIS (Confidence: 87%)                               |  |
|        |  |  The host exposes RDP (TCP/3389) without Network Level      |  |
|        |  |  Authentication (NLA) enabled. This allows unauthenticated|  |
|        |  |  access to the login screen, increasing brute-force risk.   |  |
|        |  |                                                              |  |
|        |  |  **Verification Steps:**                                    |  |
|        |  |  1. Run: `nmap -p 3389 --script rdp-enum-encryption <target>`|  |
|        |  |  2. Check Group Policy: Require user authentication for RDP |  |
|        |  |  3. Attempt connection with xfreerdp / Remmina            |  |
|        |  +--------------------------------------------------------------+  |
|        |                                                                      |
+--------+--------------------------------------------------------------------+
```


---

# 8. DEVELOPMENT ROADMAP

## Phase 0: Foundation (Weeks 1-3)
**Goal**: Establish development environment, core infrastructure, and project skeleton.

| Week | Deliverables |
|------|-----------|
| W1 | Dev environment setup (Tauri v2, FastAPI, OpenVINO), monorepo structure, CI/CD pipeline |
| W2 | Database schema implementation (SQLAlchemy models), Alembic migrations, basic CRUD APIs |
| W3 | Tauri shell with React frontend, routing, dark theme system, sidebar navigation |

## Phase 1: Core Platform (Weeks 4-7)
**Goal**: Working chat, project management, file handling, and AI inference pipeline.

| Week | Deliverables |
|------|-----------|
| W4 | OpenVINO inference manager, Phi-4 Mini INT4 loading, streaming chat API |
| W5 | Chat UI with markdown, code highlighting, file upload, streaming display |
| W6 | Project memory system, context injection, conversation branching |
| W7 | File encryption, storage abstraction, drag-and-drop upload, settings panel |

## Phase 2: Reconnaissance Intelligence (Weeks 8-11)
**Goal**: Ingest and analyze outputs from all major reconnaissance tools.

| Week | Deliverables |
|------|-----------|
| W8 | Nmap, Masscan, RustScan parsers; host/service database population |
| W9 | HTTPX, Amass, Subfinder, DNSX, Naabu parsers; subdomain enumeration view |
| W10 | Katana, Gau, Wayback URLs, FFUF, Gobuster, Dirsearch parsers; endpoint discovery |
| W11 | WhatWeb, Nikto, Nuclei parsers; attack surface analysis AI; prioritization engine |

## Phase 3: Security Analysis Modules (Weeks 12-16)
**Goal**: Web security, source code, JavaScript, and log analysis.

| Week | Deliverables |
|------|-----------|
| W12 | Burp Suite import, HTTP request/response analyzer, JWT/OAuth/SAML detectors |
| W13 | GraphQL introspection analyzer, OpenAPI security review, web security dashboard |
| W14 | Source code upload (ZIP/git), Python/Go/Java analyzers, dependency graph |
| W15 | JavaScript/TypeScript/PHP/Ruby/Node analyzers, secret detection, endpoint extraction |
| W16 | Log parsers (Suricata, Zeek, Apache, Nginx, Windows, Sysmon), timeline builder, IOC extraction |

## Phase 4: Advanced Modules (Weeks 17-20)
**Goal**: Malware analysis, knowledge graph, evidence system, and reporting.

| Week | Deliverables |
|------|-----------|
| W17 | YARA integration, PE/ELF static analysis, behavior indicators, malware dashboard |
| W18 | Knowledge graph builder, node/edge CRUD, graph visualization, semantic search |
| W19 | Evidence system, chain of custody, confidence scoring, verification workflow |
| W20 | Report generator (Markdown/PDF/DOCX), executive summary AI, risk calculator |

## Phase 5: Polish & Hardening (Weeks 21-24)
**Goal**: Performance optimization, security hardening, Windows packaging, documentation.

| Week | Deliverables |
|------|-----------|
| W21 | NPU optimization, model caching, memory profiling, streaming performance tuning |
| W22 | Security audit, input sanitization, encryption verification, penetration testing |
| W23 | Windows installer (NSIS), auto-updater, code signing, offline documentation |
| W24 | User manual, API documentation, video tutorials, community release |

---

# 9. MILESTONE PLAN

## Milestone 1: "Ignition" — Core Platform (End of Week 7)
**Definition of Done:**
- [ ] Tauri desktop app launches on Windows 11
- [ ] FastAPI backend serves REST + WebSocket APIs
- [ ] SQLite database with full schema operational
- [ ] Phi-4 Mini INT4 loads via OpenVINO and responds to prompts
- [ ] Chat UI supports markdown, code blocks, file upload, streaming
- [ ] Project CRUD with scope definition
- [ ] Settings panel with model configuration
- [ ] All code linted (Ruff), tested (Pytest), typed (TypeScript strict)

**Review Gate**: Architecture review, performance baseline, security threat model.

## Milestone 2: "Recon" — Attack Surface Mapping (End of Week 11)
**Definition of Done:**
- [ ] 16 reconnaissance tool parsers implemented and tested
- [ ] Host/service database auto-populates from tool outputs
- [ ] AI analyzes attack surface and generates recommendations
- [ ] Recon dashboard with sortable/filterable host tables
- [ ] Risk-based prioritization of findings
- [ ] Evidence auto-linked to parsed findings
- [ ] Project memory avoids duplicate recommendations

**Review Gate**: Parser accuracy review, AI hallucination testing, large dataset performance (10k hosts).

## Milestone 3: "Analysis" — Deep Security Inspection (End of Week 16)
**Definition of Done:**
- [ ] Web security module analyzes Burp exports and raw HTTP
- [ ] Source code analysis supports all 11 languages
- [ ] Secret detection with <5% false positive rate
- [ ] JavaScript intelligence extracts endpoints, tokens, routes
- [ ] Log intelligence generates attack timelines with MITRE mapping
- [ ] All modules produce evidence-backed findings only

**Review Gate**: Accuracy testing against known vulnerable applications, false positive review.

## Milestone 4: "Synthesis" — Intelligence & Reporting (End of Week 20)
**Definition of Done:**
- [ ] Knowledge graph correlates all project artifacts
- [ ] Interactive graph visualization with 1000+ nodes
- [ ] Evidence system with full chain of custody
- [ ] Report generator produces executive + technical reports
- [ ] Malware triage with YARA + static analysis
- [ ] Cross-module correlations (e.g., log IOCs -> knowledge graph nodes)

**Review Gate**: End-to-end workflow test, report quality review, graph performance test.

## Milestone 5: "Launch" — Production Ready (End of Week 24)
**Definition of Done:**
- [ ] NPU inference achieves <2s time-to-first-token
- [ ] Memory usage <4GB during typical operations
- [ ] Zero telemetry verified (network traffic analysis)
- [ ] Project data encrypted at rest
- [ ] Windows installer with code signing
- [ ] Documentation complete
- [ ] All milestones reviewed and signed off

**Review Gate**: Final security audit, performance acceptance, release approval.

---

# 10. INITIAL IMPLEMENTATION — SCAFFOLDING

## 10.1 Backend Core Scaffolding

### `services/helios/config.py`
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "HELIOS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./helios.db"
    DATABASE_POOL_SIZE: int = 20

    # Vector Database
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # AI / OpenVINO
    OV_MODEL_PATH: str = "./models/phi-4-mini-int4"
    OV_DEVICE: str = "NPU"  # NPU, GPU, CPU fallback
    OV_MAX_CONTEXT: int = 128000
    OV_TEMPERATURE: float = 0.1  # Low temp for security analysis
    OV_TOP_P: float = 0.9

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ENCRYPTION_KEY_PATH: str = "./data/keys"
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536

    # Storage
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### `services/helios/main.py`
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from helios.config import get_settings
from helios.infrastructure.database import init_db
from helios.infrastructure.openvino_runtime import OpenVINORuntime
from helios.api.router import api_router
from helios.lifespan import lifespan

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "npu_available": OpenVINORuntime.is_npu_available(),
    }
```

### `services/helios/infrastructure/openvino_runtime.py`
```python
import os
import logging
from pathlib import Path
from typing import AsyncIterator, Optional
import openvino as ov
from openvino.runtime import Core

logger = logging.getLogger(__name__)

class OpenVINORuntime:
    _instance: Optional["OpenVINORuntime"] = None
    _core: Optional[Core] = None
    _model: Optional[ov.CompiledModel] = None
    _device: str = "CPU"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def is_npu_available(cls) -> bool:
        if cls._core is None:
            cls._core = Core()
        return "NPU" in cls._core.available_devices

    def load_model(self, model_path: str, device: str = "NPU") -> None:
        if self._core is None:
            self._core = Core()

        # Fallback: NPU -> GPU -> CPU
        preferred_devices = [device]
        if device == "NPU":
            preferred_devices = ["NPU", "GPU", "CPU"]

        available = self._core.available_devices
        selected_device = None
        for dev in preferred_devices:
            if dev in available:
                selected_device = dev
                break

        if selected_device is None:
            selected_device = "CPU"

        self._device = selected_device

        # Load OpenVINO IR model
        model_dir = Path(model_path)
        xml_path = model_dir / "openvino_model.xml"
        bin_path = model_dir / "openvino_model.bin"

        if not xml_path.exists():
            raise FileNotFoundError(f"Model not found: {xml_path}")

        model = self._core.read_model(str(xml_path), str(bin_path))

        # Compile with performance hints
        config = {
            "PERFORMANCE_HINT": "LATENCY",
            "CACHE_DIR": "./data/model_cache",
        }

        self._model = self._core.compile_model(model, selected_device, config)
        logger.info(f"Model loaded on {selected_device}")

    async def generate_stream(
        self, 
        prompt: str, 
        max_tokens: int = 2048,
        temperature: float = 0.1,
    ) -> AsyncIterator[str]:
        if self._model is None:
            raise RuntimeError("Model not loaded")

        # Tokenize input (simplified — actual implementation uses tokenizer)
        # This is a placeholder for the actual inference pipeline
        # Real implementation would use Optimum Intel + transformers pipeline

        infer_request = self._model.create_infer_request()

        # Streaming generation logic
        # Actual implementation uses KV-cache optimized generation
        yield "[Model response would stream here]"

    def get_status(self) -> dict:
        return {
            "device": self._device,
            "loaded": self._model is not None,
            "npu_available": self.is_npu_available(),
        }
```

### `services/helios/api/v1/chat.py`
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Optional
import json
import logging

from helios.schemas.chat import ChatMessageCreate, ChatMessageResponse
from helios.core.chat.engine import ChatEngine
from helios.infrastructure.openvino_runtime import OpenVINORuntime

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["chat"])
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[project_id] = websocket

    def disconnect(self, project_id: str):
        self.active_connections.pop(project_id, None)

    async def send_token(self, project_id: str, token: str):
        if ws := self.active_connections.get(project_id):
            await ws.send_json({"type": "chat.token", "token": token})

manager = ConnectionManager()

@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, project_id: str):
    await manager.connect(project_id, websocket)
    runtime = OpenVINORuntime()
    engine = ChatEngine(project_id=project_id)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "chat.message":
                message_id = data.get("message_id")
                content = data.get("content")
                attachments = data.get("attachments", [])

                # Save user message
                await engine.add_message(role="user", content=content)

                # Stream AI response
                full_response = ""
                async for token in engine.generate_response(
                    content, 
                    attachments=attachments,
                    runtime=runtime
                ):
                    full_response += token
                    await manager.send_token(project_id, token)

                # Save assistant message
                await engine.add_message(role="assistant", content=full_response)

                # Signal completion
                await websocket.send_json({
                    "type": "chat.complete",
                    "message_id": message_id,
                })

    except WebSocketDisconnect:
        manager.disconnect(project_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"type": "chat.error", "error": str(e)})
        manager.disconnect(project_id)

@router.get("/messages", response_model=list[ChatMessageResponse])
async def get_chat_history(project_id: str, limit: int = 100):
    engine = ChatEngine(project_id=project_id)
    return await engine.get_history(limit=limit)

@router.post("/messages", response_model=ChatMessageResponse)
async def create_message(project_id: str, message: ChatMessageCreate):
    engine = ChatEngine(project_id=project_id)
    return await engine.add_message(role=message.role, content=message.content)
```

## 10.2 Frontend Core Scaffolding

### `apps/web/src/features/chat/ChatPanel.tsx`
```typescript
import { useState, useRef, useCallback } from 'react';
import { useChat } from '@/hooks/useChat';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { FileUpload } from '@/components/chat/FileUpload';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Paperclip, Image as ImageIcon } from 'lucide-react';

interface ChatPanelProps {
  projectId: string;
}

export function ChatPanel({ projectId }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, isStreaming, sendMessage, stopGeneration } = useChat(projectId);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() && attachments.length === 0) return;

    const content = input.trim();
    setInput('');

    await sendMessage({
      content,
      attachments,
      streaming: true,
    });

    setAttachments([]);
  }, [input, attachments, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg-primary">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            role={msg.role}
            content={msg.content}
            citations={msg.metadata?.citations}
            isStreaming={msg.isStreaming}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border-default p-4 bg-bg-secondary">
        {attachments.length > 0 && (
          <div className="flex gap-2 mb-2 flex-wrap">
            {attachments.map((file, i) => (
              <FileUpload.Badge 
                key={i} 
                filename={file.name} 
                onRemove={() => setAttachments(prev => prev.filter((_, idx) => idx !== i))}
              />
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <div className="flex gap-1">
            <Button variant="ghost" size="icon" className="text-muted-foreground">
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="text-muted-foreground">
              <ImageIcon className="h-4 w-4" />
            </Button>
          </div>

          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask HELIOS about your project..."
            className="min-h-[44px] max-h-[200px] resize-none bg-bg-tertiary border-border-default"
            rows={1}
          />

          {isStreaming ? (
            <Button 
              variant="destructive" 
              size="icon"
              onClick={stopGeneration}
            >
              <span className="h-2 w-2 bg-white rounded-sm" />
            </Button>
          ) : (
            <Button 
              variant="default" 
              size="icon"
              onClick={handleSubmit}
              disabled={!input.trim() && attachments.length === 0}
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
```

### `apps/web/src/hooks/useChat.ts`
```typescript
import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatService } from '@/services/chatService';
import { useWebSocket } from './useWebSocket';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: {
    citations?: Array<{ evidenceId: string; snippet: string }>;
    model?: string;
    tokensUsed?: number;
  };
  isStreaming?: boolean;
}

interface SendMessageParams {
  content: string;
  attachments?: File[];
  streaming?: boolean;
}

export function useChat(projectId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const streamingMessageRef = useRef<string>('');
  const queryClient = useQueryClient();

  // Load initial history
  const { data: history } = useQuery({
    queryKey: ['chat', projectId, 'history'],
    queryFn: () => chatService.getHistory(projectId),
  });

  useEffect(() => {
    if (history) {
      setMessages(history);
    }
  }, [history]);

  // WebSocket for streaming
  const { send, lastMessage } = useWebSocket(`/ws/v1/projects/${projectId}/chat`);

  useEffect(() => {
    if (!lastMessage) return;

    const data = JSON.parse(lastMessage.data);

    switch (data.type) {
      case 'chat.token':
        streamingMessageRef.current += data.token;
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant' && last.isStreaming) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: streamingMessageRef.current }
            ];
          }
          return [
            ...prev,
            {
              id: `streaming-${Date.now()}`,
              role: 'assistant',
              content: streamingMessageRef.current,
              isStreaming: true,
            }
          ];
        });
        break;

      case 'chat.complete':
        setIsStreaming(false);
        streamingMessageRef.current = '';
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.isStreaming) {
            return [...prev.slice(0, -1), { ...last, isStreaming: false }];
          }
          return prev;
        });
        queryClient.invalidateQueries({ queryKey: ['chat', projectId] });
        break;

      case 'chat.error':
        setIsStreaming(false);
        streamingMessageRef.current = '';
        // Handle error state
        break;
    }
  }, [lastMessage, projectId, queryClient]);

  const sendMessage = useCallback(async (params: SendMessageParams) => {
    // Optimistically add user message
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: params.content,
    };

    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);
    streamingMessageRef.current = '';

    // Upload attachments if any
    let attachmentIds: string[] = [];
    if (params.attachments && params.attachments.length > 0) {
      const uploads = await Promise.all(
        params.attachments.map(file => chatService.uploadFile(projectId, file))
      );
      attachmentIds = uploads.map(u => u.id);
    }

    // Send via WebSocket
    send({
      type: 'chat.message',
      message_id: userMessage.id,
      content: params.content,
      attachments: attachmentIds,
      streaming: params.streaming ?? true,
    });
  }, [projectId, send]);

  const stopGeneration = useCallback(() => {
    send({ type: 'chat.stop' });
    setIsStreaming(false);
  }, [send]);

  return {
    messages,
    isStreaming,
    sendMessage,
    stopGeneration,
  };
}
```

## 10.3 Tauri Desktop Shell

### `apps/desktop/src/main.rs`
```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, SystemTray, SystemTrayEvent, SystemTrayMenu, SystemTrayMenuItem};

mod tray;
mod fs_watcher;
mod encryption;

fn main() {
    let tray_menu = SystemTrayMenu::new()
        .add_item(SystemTrayMenuItem::new("Show HELIOS", "show"))
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(SystemTrayMenuItem::new("Quit", "quit"));

    let system_tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .system_tray(system_tray)
        .on_system_tray_event(tray::handle_tray_event)
        .setup(|app| {
            // Initialize encryption keystore
            encryption::init_keystore(app.handle())?;

            // Start file system watcher for project directories
            fs_watcher::init_watcher(app.handle())?;

            // Ensure data directories exist
            let app_dir = app.path_resolver().app_data_dir().unwrap();
            std::fs::create_dir_all(app_dir.join("projects"))?;
            std::fs::create_dir_all(app_dir.join("uploads"))?;
            std::fs::create_dir_all(app_dir.join("models"))?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            encryption::encrypt_file,
            encryption::decrypt_file,
            fs_watcher::watch_directory,
            fs_watcher::unwatch_directory,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

---

# 11. SECURITY CONSIDERATIONS

## 11.1 Data Protection
- **At-Rest Encryption**: All project files encrypted with AES-256-GCM using project-specific keys derived via Argon2id
- **In-Transit**: WebSocket over TLS (wss://) even for localhost to prevent local MitM
- **Memory Safety**: Rust (Tauri) for native code, no unsafe Rust in security-critical paths
- **Sanitization**: All file uploads scanned for executable content, MIME type verified, magic bytes checked

## 11.2 AI Safety
- **Hallucination Mitigation**: Every AI conclusion requires explicit evidence linkage
- **Confidence Scoring**: All AI outputs include confidence levels (High/Medium/Low)
- **Human-in-the-Loop**: No automated exploitation; all findings marked "Observed" until human verification
- **Prompt Injection Defense**: Strict system prompt boundaries, input sanitization, no tool execution from AI output

## 11.3 Operational Security
- **Zero Telemetry**: No outbound network calls except explicit user actions (e.g., downloading models)
- **No Cloud Dependencies**: All AI inference local; no API keys for external LLMs
- **Audit Logging**: Every action logged to tamper-resistant event store
- **Scope Enforcement**: AI context explicitly bounded by project scope definition

---

# 12. PERFORMANCE TARGETS

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to First Token | <2s | From prompt submission to first streamed token |
| Token Generation Rate | >15 tok/s | Sustained on Intel Core Ultra 5 125H NPU |
| Memory Footprint | <4GB | Peak RAM during typical operations |
| Startup Time | <5s | From app launch to interactive UI |
| Database Query | <100ms | P95 for complex graph queries |
| File Upload | <2s/100MB | Encrypted upload to local storage |
| Report Generation | <30s | Full PDF report with 50 findings |

---

# 13. TESTING STRATEGY

## 13.1 Backend Testing
- **Unit Tests**: 80%+ coverage on all service classes using pytest + pytest-asyncio
- **Integration Tests**: FastAPI TestClient for all API endpoints
- **Parser Tests**: Golden file testing for all 16+ recon tool parsers
- **AI Tests**: Ground-truth datasets for security analysis accuracy
- **Property-Based Tests**: Hypothesis for input validation edge cases

## 13.2 Frontend Testing
- **Component Tests**: Vitest + React Testing Library for UI components
- **E2E Tests**: Playwright for critical user flows (chat -> recon -> report)
- **Visual Regression**: Chromatic for UI consistency
- **Accessibility**: axe-core for WCAG 2.1 AA compliance

## 13.3 Security Testing
- **SAST**: Semgrep rules for Python and TypeScript security patterns
- **DAST**: OWASP ZAP baseline scan against running application
- **Dependency Scanning**: pip-audit + npm audit in CI
- **Fuzzing**: Atheris for Python parser fuzzing

---

# APPENDIX A: OPENVINO MODEL PREPARATION

```bash
# 1. Install Optimum Intel
pip install optimum[openvino] transformers

# 2. Download and convert Phi-4 Mini
optimum-cli export openvino   --model microsoft/Phi-4-mini-instruct   --task text-generation-with-past   --weight-format int4   --sym   --group-size 128   --ratio 0.8   --trust-remote-code   ./models/phi-4-mini-int4

# 3. Verify NPU compatibility
python -c "
from openvino import Core
core = Core()
print('Available devices:', core.available_devices)
model = core.read_model('./models/phi-4-mini-int4/openvino_model.xml')
compiled = core.compile_model(model, 'NPU')
print('NPU compilation successful')
"
```

---

# APPENDIX B: KEYBOARD SHORTCUTS

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+H` | Toggle sidebar |
| `Ctrl+Shift+C` | Focus chat input |
| `Ctrl+Shift+R` | Open recon view |
| `Ctrl+Shift+G` | Open knowledge graph |
| `Ctrl+Shift+E` | Open evidence panel |
| `Ctrl+Shift+T` | New tab |
| `Ctrl+W` | Close tab |
| `Ctrl+Shift+F` | Global search |
| `Ctrl+Shift+U` | Upload file |
| `Ctrl+Shift+S` | Save project |
| `Ctrl+Shift+X` | Export report |
| `Ctrl+Shift+I` | Import tool output |
| `Ctrl+Shift+M` | Toggle dark/light mode |
| `Ctrl+Shift+D` | Toggle developer tools |
| `Ctrl+Q` | Quit application |

---

*End of Blueprint Document*
