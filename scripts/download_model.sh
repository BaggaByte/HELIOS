#!/usr/bin/env bash
# HELIOS — OpenVINO Model Setup (Linux / macOS)
#
# Downloads and converts the Phi-4-mini model to OpenVINO INT4 format,
# or verifies an existing model. The default output path matches config.py's
# OV_MODEL_PATH so the backend finds the model automatically on first launch.
#
# Usage:
#   bash scripts/download_model.sh
#   bash scripts/download_model.sh --device CPU
#   bash scripts/download_model.sh --output /custom/path/to/model

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
MODEL_ID="microsoft/Phi-4-mini-instruct"
DEVICE="CPU"
OUTPUT_DIR=""

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)   MODEL_ID="$2";   shift 2 ;;
        --device)  DEVICE="$2";     shift 2 ;;
        --output)  OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--model MODEL_ID] [--device DEVICE] [--output DIR]"
            exit 0
            ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# ── Resolve output path to match config.py's get_app_data_dir() ─────────────
if [[ -z "$OUTPUT_DIR" ]]; then
    OS="$(uname -s)"
    if [[ "$OS" == "Darwin" ]]; then
        # macOS: ~/Library/Application Support/com.baggabyte.helios
        BASE="${HOME}/Library/Application Support/com.baggabyte.helios"
    else
        # Linux XDG: ~/.local/share/com.baggabyte.helios
        BASE="${XDG_DATA_HOME:-${HOME}/.local/share}/com.baggabyte.helios"
    fi
    OUTPUT_DIR="${BASE}/models/phi4_mini_int4_ov"
fi

echo ""
echo "================================================"
echo " HELIOS — OpenVINO Model Setup"
echo "================================================"
echo " Model  : ${MODEL_ID}"
echo " Output : ${OUTPUT_DIR}"
echo " Device : ${DEVICE}"
echo ""

# ── Check if model already present ───────────────────────────────────────────
model_valid() {
    [[ -f "${OUTPUT_DIR}/openvino_model.xml" ]] &&
    [[ -f "${OUTPUT_DIR}/openvino_model.bin" ]] &&
    [[ -f "${OUTPUT_DIR}/tokenizer.json" ]]
}

if model_valid; then
    echo "✅  Model already present at '${OUTPUT_DIR}'"
    echo "    Skipping download. Running verification..."
else
    echo "⬇️   Model not found. Starting download & conversion..."
    echo "    This may take 10–30 minutes depending on your connection."
    echo ""

    # Check optimum-cli
    if ! command -v optimum-cli &>/dev/null; then
        echo "❌  optimum-cli not found. Install with:"
        echo "    uv add optimum[openvino]"
        echo "    Then re-run this script."
        exit 1
    fi

    mkdir -p "${OUTPUT_DIR}"

    echo "Converting '${MODEL_ID}' to OpenVINO IR (INT4)..."
    optimum-cli export openvino \
        --model "${MODEL_ID}" \
        --task text-generation-with-past \
        --weight-format int4 \
        --sym \
        --group-size -1 \
        --ratio 1.0 \
        --trust-remote-code \
        "${OUTPUT_DIR}"

    echo ""
    echo "✅  Conversion complete."
fi

# ── Verify the model loads ────────────────────────────────────────────────────
echo ""
echo "🔍  Verifying model loads on '${DEVICE}'..."

python3 - <<PYEOF
import sys
from pathlib import Path

try:
    import openvino_genai as ov_genai
except ImportError:
    print("WARN: openvino_genai not installed — skipping runtime verification.")
    print("      Install with:  uv add openvino-genai")
    sys.exit(0)

model_dir = Path("${OUTPUT_DIR}")
if not model_dir.exists():
    print(f"ERROR: model directory not found: {model_dir}")
    sys.exit(1)

print(f"Loading pipeline from {model_dir} on ${DEVICE} ...")
try:
    pipe = ov_genai.LLMPipeline(str(model_dir), "${DEVICE}")
    print("Model loaded. Running smoke-test inference...")
    result = pipe.generate(
        "<|system|>\nYou are a security assistant.<|end|>\n"
        "<|user|>\nSay 'ok'<|end|>\n<|assistant|>\n",
        max_new_tokens=10
    )
    print(f"Response: {result}")
    print("SUCCESS: Model is functional.")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
PYEOF

echo ""
echo "================================================"
echo " Model is ready at:"
echo "   ${OUTPUT_DIR}"
echo ""
echo " Start the backend with:"
echo "   cd services"
echo "   uv run uvicorn helios.main:app --reload"
echo "================================================"
echo ""
