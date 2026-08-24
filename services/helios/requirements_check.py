"""
Environment requirements checker for HELIOS.

Run with:  python -m helios.requirements_check
"""

import sys
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


def main() -> int:
    print("\n========================================")
    print(" HELIOS — Environment Check")
    print("========================================\n")

    all_ok = True

    # Python version
    ok = sys.version_info >= (3, 12)
    print(f"  {'✅' if ok else '❌'}  Python {sys.version_info.major}.{sys.version_info.minor} (need ≥ 3.12)")
    all_ok = all_ok and ok

    # Required packages
    packages = [
        ("fastapi",            lambda: __import__("fastapi")),
        ("uvicorn",            lambda: __import__("uvicorn")),
        ("sqlalchemy",         lambda: __import__("sqlalchemy")),
        ("aiosqlite",          lambda: __import__("aiosqlite")),
        ("alembic",            lambda: __import__("alembic")),
        ("pydantic_settings",  lambda: __import__("pydantic_settings")),
        ("chromadb",           lambda: __import__("chromadb")),
        ("sentence_transformers", lambda: __import__("sentence_transformers")),
        ("cryptography",       lambda: __import__("cryptography")),
        ("lief",               lambda: __import__("lief")),
        ("yara",               lambda: __import__("yara")),
    ]

    for name, importer in packages:
        all_ok = _check(name, importer) and all_ok

    # Optional but important
    print("\n  Optional (AI inference):")
    try:
        import openvino_genai  # type: ignore  # noqa: F401
        print("  ✅  openvino_genai")
    except ImportError:
        print("  ⚠️   openvino_genai not installed — mock mode only")

    try:
        from openvino import Core  # type: ignore
        core = Core()
        devices = core.available_devices
        npu = "NPU" in devices
        print(f"  ✅  openvino  (devices: {', '.join(devices)})")
        print(f"  {'✅' if npu else '⚠️ '}  NPU {'available' if npu else 'not detected (CPU/GPU will be used)'}")
    except Exception as exc:
        print(f"  ⚠️   openvino: {exc}")

    # Model files
    print("\n  Model files:")
    model_dir = Path(__file__).parent.parent.parent / "models" / "phi-4-mini-openvino"
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

    # .env file
    print("\n  Configuration:")
    env_path = Path(__file__).parent.parent / ".env"
    env_exists = env_path.exists()
    print(f"  {'✅' if env_exists else '❌'}  .env file {'found' if env_exists else 'missing — copy .env.example to .env'}")

    print("\n========================================")
    if all_ok and model_ok and env_exists:
        print(" ✅  All checks passed. Ready to start.\n")
    else:
        print(" ⚠️  Some checks failed. See above.\n")
    print("========================================\n")

    return 0 if (all_ok and model_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
