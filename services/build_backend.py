"""
build_backend.py — PyInstaller sidecar builder for HELIOS.

Usage
─────
  # Auto-detect target from host platform (CI default)
  python build_backend.py

  # Explicit target triple (required for cross-compilation)
  python build_backend.py --target x86_64-apple-darwin

Supported Tauri target triples
───────────────────────────────
  x86_64-pc-windows-msvc        Windows x64
  aarch64-apple-darwin          macOS Apple Silicon
  x86_64-apple-darwin           macOS Intel
  x86_64-unknown-linux-gnu      Linux x64
  aarch64-unknown-linux-gnu     Linux ARM64
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ── Supported targets ───────────────────────────────────────────────────────

_TARGET_EXT: dict[str, str] = {
    "x86_64-pc-windows-msvc": ".exe",
    "aarch64-apple-darwin": "",
    "x86_64-apple-darwin": "",
    "x86_64-unknown-linux-gnu": "",
    "aarch64-unknown-linux-gnu": "",
}


def _detect_target() -> str:
    """Infer the target triple from the current runtime platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        return "x86_64-pc-windows-msvc"
    if system == "darwin":
        return (
            "aarch64-apple-darwin"
            if machine in ("arm64", "aarch64")
            else "x86_64-apple-darwin"
        )
    # Linux
    return (
        "aarch64-unknown-linux-gnu"
        if machine in ("aarch64", "arm64")
        else "x86_64-unknown-linux-gnu"
    )


def _pyinstaller_sep() -> str:
    """Return the PyInstaller --add-data separator for the current OS."""
    return ";" if sys.platform == "win32" else ":"


def build(target: str | None = None) -> None:
    base_dir = Path(__file__).parent.resolve()

    if target is None:
        target = _detect_target()

    if target not in _TARGET_EXT:
        print(
            f"ERROR: Unknown target triple '{target}'.\n"
            f"Supported targets: {list(_TARGET_EXT)}"
        )
        sys.exit(1)

    ext = _TARGET_EXT[target]
    sep = _pyinstaller_sep()

    bin_name = f"helios_backend-{target}{ext}"
    output_dir = base_dir.parent / "apps" / "desktop"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building sidecar for target: {target}")
    print(f"  Output binary : {output_dir / bin_name}")
    print(f"  add-data sep  : '{sep}' (platform: {sys.platform})")

    alembic_ini = base_dir / "alembic.ini"
    alembic_dir = base_dir / "alembic"

    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "helios/main.py",
        "--name=helios_backend",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--distpath=dist",
        f"--paths={base_dir}",
        "--hidden-import=uvicorn",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=fastapi",
        "--hidden-import=alembic",
        "--hidden-import=aiosqlite",
        "--hidden-import=sqlalchemy.dialects.sqlite",
        f"--add-data={alembic_ini}{sep}.",
        f"--add-data={alembic_dir}{sep}alembic",
        # Exclude heavy ML packages that are not needed at runtime when model
        # files are absent — they can be installed separately.
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "--exclude-module=transformers",
        "--exclude-module=openvino",
        "--exclude-module=openvino_genai",
        "--exclude-module=scipy",
    ]

    # --windowed suppresses the console on Windows; on Linux/macOS it is a
    # no-op (or unsupported) — skip it on those platforms.
    if sys.platform == "win32":
        pass

    print("\nRunning PyInstaller...\n")
    result = subprocess.run(pyinstaller_args, cwd=str(base_dir), check=False)
    if result.returncode != 0:
        print(f"\nERROR: PyInstaller exited with code {result.returncode}")
        sys.exit(result.returncode)

    # ── Copy and rename to the Tauri-expected filename ─────────────────────
    src_exe = base_dir / "dist" / f"helios_backend{ext}"
    dst_exe = output_dir / bin_name

    if not src_exe.exists():
        print(f"\nERROR: Expected sidecar at {src_exe} — not found after build.")
        sys.exit(1)

    shutil.copy2(src_exe, dst_exe)
    print(f"\nSidecar ready: {dst_exe}")

    # Verify the produced file is the right architecture on macOS
    if sys.platform == "darwin":
        _verify_macos_arch(dst_exe, target)


def _verify_macos_arch(binary: Path, target: str) -> None:
    """Run `lipo -archs` and confirm the binary matches the expected target."""
    expected_arch = "arm64" if "aarch64" in target else "x86_64"
    try:
        out = subprocess.check_output(
            ["lipo", "-archs", str(binary)], stderr=subprocess.DEVNULL
        )
        arch_str = out.decode().strip()
        if expected_arch not in arch_str:
            print(
                f"WARNING: Binary architecture '{arch_str}' does not match "
                f"expected '{expected_arch}' for target '{target}'.\n"
                f"  Pass --target explicitly or build on a matching runner."
            )
        else:
            print(f"  Architecture verified: {arch_str} ✓")
    except Exception as e:
        print(f"  (Could not verify architecture via lipo: {e})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build the HELIOS backend PyInstaller sidecar."
    )
    parser.add_argument(
        "--target",
        metavar="TRIPLE",
        help=(
            "Explicit Tauri target triple (e.g. x86_64-apple-darwin). "
            "Auto-detected from the current platform when omitted."
        ),
    )
    args = parser.parse_args()
    build(target=args.target)
