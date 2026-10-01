"""
Environment requirements checker for HELIOS.

Run with:  python -m helios.requirements_check

Checks:
  1. Python version
  2. Required Python packages
  3. Optional AI packages (openvino, openvino_genai)
  4. Model files on disk
  5. External binary tools (nmap, nuclei, subfinder, etc.)
  6. Redis / Celery connectivity
  7. .env configuration file
"""

import sys
import shutil
import io

# Ensure stdout can emit UTF-8 emoji on Windows cp1252 terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass
from pathlib import Path


def _check(label: str, fn):
    try:
        result = fn()
        status = "✅" if result else "⚠️ "
        print(f"  {status}  {label}")
        return result
    except Exception as exc:
        print(f"  ❌  {label}  ({exc})")
        return False


def _check_binary(name: str, install_hint: str = "") -> bool:
    found = shutil.which(name) is not None
    hint = f" — {install_hint}" if install_hint and not found else ""
    print(f"  {'✅' if found else '⚠️ '}  {name}{hint}")
    return found


def main() -> int:
    print("\n========================================")
    print(" HELIOS — Environment Check")
    print("========================================\n")

    all_ok = True

    # ── Python version ────────────────────────────────────────────────────────
    ok = sys.version_info >= (3, 13)
    print(
        f"  {'✅' if ok else '❌'}  Python {sys.version_info.major}.{sys.version_info.minor} (need ≥ 3.13)"
    )
    all_ok = all_ok and ok

    # ── Required Python packages ──────────────────────────────────────────────
    print("\n  Required Python packages:")
    packages = [
        ("fastapi", lambda: __import__("fastapi")),
        ("uvicorn", lambda: __import__("uvicorn")),
        ("sqlalchemy", lambda: __import__("sqlalchemy")),
        ("aiosqlite", lambda: __import__("aiosqlite")),
        ("alembic", lambda: __import__("alembic")),
        ("pydantic_settings", lambda: __import__("pydantic_settings")),
        ("chromadb", lambda: __import__("chromadb")),
        ("sentence_transformers", lambda: __import__("sentence_transformers")),
        ("cryptography", lambda: __import__("cryptography")),
        ("lief", lambda: __import__("lief")),
        ("yara", lambda: __import__("yara")),
    ]
    for name, importer in packages:
        all_ok = _check(name, importer) and all_ok

    # ── Optional background task dependencies ────────────────────────────────
    print("\n  Background tasks (Redis + Celery):")
    celery_ok = _check("celery", lambda: __import__("celery"))
    redis_ok = _check("redis (python client)", lambda: __import__("redis"))
    if celery_ok and redis_ok:
        try:
            import redis as _redis  # type: ignore

            r = _redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
            r.ping()
            print("  ✅  Redis server reachable at localhost:6379")
        except Exception as exc:
            print(
                f"  ⚠️   Redis server not reachable ({exc}) — tasks will run synchronously"
            )

    # ── Optional AI packages ──────────────────────────────────────────────────
    print("\n  AI inference (optional):")
    try:
        import openvino_genai  # type: ignore  # noqa: F401

        print("  ✅  openvino_genai")
    except ImportError:
        print("  ⚠️   openvino_genai not installed — AI will run in mock mode")
        print("       Install:  uv add openvino-genai")

    try:
        from openvino import Core  # type: ignore

        core = Core()
        devices = core.available_devices
        npu = "NPU" in devices
        print(f"  ✅  openvino  (devices: {', '.join(devices)})")
        print(
            f"  {'✅' if npu else '⚠️ '}  NPU {'available' if npu else 'not detected (CPU/GPU fallback)'}"
        )
    except Exception as exc:
        print(f"  ⚠️   openvino: {exc}")

    # ── Model files ───────────────────────────────────────────────────────────
    print("\n  AI model files:")
    model_dir = Path(__file__).parent.parent.parent / "models" / "phi4_mini_int4_ov"
    required_model_files = [
        "openvino_model.xml",
        "openvino_model.bin",
        "tokenizer.json",
        "openvino_tokenizer.xml",
        "openvino_detokenizer.xml",
    ]
    model_ok = True
    for f in required_model_files:
        exists = (model_dir / f).exists()
        print(f"  {'✅' if exists else '❌'}  {f}")
        if not exists:
            model_ok = False

    if not model_ok:
        print("\n  ⚠️  Model missing — run:  powershell scripts/download_model.ps1")

    # ── External security tool binaries ──────────────────────────────────────
    print("\n  External security tools:")
    print("  [Core — required for full functionality]")
    _check_binary("nmap", "https://nmap.org/download.html")

    print("  [ProjectDiscovery toolkit]")
    _check_binary(
        "nuclei", "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
    )
    _check_binary(
        "subfinder",
        "go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    )
    _check_binary(
        "httpx", "go install github.com/projectdiscovery/httpx/cmd/httpx@latest"
    )
    _check_binary(
        "naabu", "go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"
    )
    _check_binary(
        "katana", "go install github.com/projectdiscovery/katana/cmd/katana@latest"
    )
    _check_binary("dnsx", "go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest")

    print("  [OSINT / passive recon]")
    _check_binary("amass", "go install github.com/owasp-amass/amass/v4/...@master")
    _check_binary("gau", "go install github.com/lc/gau/v2/cmd/gau@latest")

    print("  [Web fuzzing / scanning]")
    _check_binary("ffuf", "go install github.com/ffuf/ffuf/v2@latest")
    _check_binary("gobuster", "go install github.com/OJ/gobuster/v3@latest")
    _check_binary(
        "dirsearch",
        "pip install dirsearch  OR  https://github.com/maurosoria/dirsearch",
    )
    _check_binary("nikto", "https://cirt.net/Nikto2")
    _check_binary(
        "whatweb", "gem install whatweb  OR  https://github.com/urbanadventurer/WhatWeb"
    )

    print("  [Port scanners]")
    _check_binary("masscan", "https://github.com/robertdavidgraham/masscan")
    _check_binary(
        "rustscan", "cargo install rustscan  OR  https://github.com/RustScan/RustScan"
    )

    # ── .env file ─────────────────────────────────────────────────────────────
    print("\n  Configuration:")
    env_path = Path(__file__).parent.parent / ".env"
    env_exists = env_path.exists()
    print(
        f"  {'✅' if env_exists else '❌'}  .env {'found' if env_exists else 'missing — copy .env.example to .env'}"
    )

    print("\n========================================")
    if all_ok and model_ok and env_exists:
        print(" ✅  All checks passed. Ready to start.\n")
    else:
        print(" ⚠️  Some checks failed or optional tools are missing. See above.\n")
    print("========================================\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
