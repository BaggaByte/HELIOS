<#
.SYNOPSIS
    Downloads and converts the Phi-4-mini model to OpenVINO INT4 format,
    or verifies the existing model if it's already present.

.DESCRIPTION
    Uses Optimum Intel (optimum-cli) to export the model from HuggingFace Hub
    into OpenVINO IR format with INT4 weight compression.

    Required GPU/NPU VRAM for conversion: ~4 GB
    Output size (INT4): ~2.1 GB

    The default output path matches config.py's OV_MODEL_PATH so the backend
    finds the model automatically without any manual configuration.

.PARAMETER ModelId
    HuggingFace model ID. Defaults to microsoft/Phi-4-mini-instruct.

.PARAMETER OutputDir
    Where to save the converted model.
    Defaults to %APPDATA%\com.baggabyte.helios\models\phi4_mini_int4_ov
    (matching the installed-app app-data path in config.py).

.PARAMETER Device
    OpenVINO device to verify with. Defaults to CPU (always available).

.EXAMPLE
    .\scripts\download_model.ps1
    .\scripts\download_model.ps1 -Device NPU
    .\scripts\download_model.ps1 -OutputDir "D:\my_models\helios"
#>

param(
    [string]$ModelId   = "microsoft/Phi-4-mini-instruct",
    [string]$Device    = "CPU",
    # Default output directory matches config.py get_app_data_dir() / OV_MODEL_PATH:
    #   Installed : %APPDATA%\com.baggabyte.helios\models\phi4_mini_int4_ov
    #   Dev server: <cwd>\data\models\phi4_mini_int4_ov
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

# ── Resolve output path to match config.py's get_app_data_dir() ─────────────
if (-not $OutputDir) {
    $appData = $env:APPDATA
    if ($appData) {
        $OutputDir = Join-Path $appData "com.baggabyte.helios\models\phi4_mini_int4_ov"
    } else {
        # Dev fallback: services/data/models/ relative to this script
        $OutputDir = Join-Path $PSScriptRoot "..\services\data\models\phi4_mini_int4_ov"
    }
}
$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " HELIOS — OpenVINO Model Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " Model  : $ModelId"
Write-Host " Output : $OutputDir"
Write-Host " Device : $Device"
Write-Host ""

# ── Helper: check if model already exists and is valid ───────────────────────
function Test-ModelValid {
    param([string]$Dir)
    if (-not (Test-Path $Dir)) { return $false }
    $xmlFiles = Get-ChildItem -Path $Dir -Filter "openvino_model.xml" -ErrorAction SilentlyContinue
    $binFiles = Get-ChildItem -Path $Dir -Filter "openvino_model.bin" -ErrorAction SilentlyContinue
    $tokFiles = Get-ChildItem -Path $Dir -Filter "tokenizer.json" -ErrorAction SilentlyContinue
    return ($xmlFiles.Count -gt 0) -and ($binFiles.Count -gt 0) -and ($tokFiles.Count -gt 0)
}

# ── Check existing model ──────────────────────────────────────────────────────
if (Test-ModelValid -Dir $OutputDir) {
    Write-Host "✅ Model already present at '$OutputDir'" -ForegroundColor Green
    Write-Host "   Skipping download. Running verification..." -ForegroundColor Gray
} else {
    Write-Host "⬇️  Model not found. Starting download & conversion..." -ForegroundColor Yellow
    Write-Host "   This may take 10-30 minutes depending on your connection." -ForegroundColor Gray
    Write-Host ""

    # Check optimum-cli is available
    $optimumPath = Get-Command optimum-cli -ErrorAction SilentlyContinue
    if (-not $optimumPath) {
        Write-Host "❌ optimum-cli not found. Install with:" -ForegroundColor Red
        Write-Host "   uv add optimum[openvino]" -ForegroundColor Yellow
        Write-Host "   Then re-run this script." -ForegroundColor Yellow
        exit 1
    }

    # Create output directory
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

    # Export with INT4 weight compression
    Write-Host "Converting '$ModelId' to OpenVINO IR (INT4)..." -ForegroundColor Cyan
    optimum-cli export openvino `
        --model $ModelId `
        --task text-generation-with-past `
        --weight-format int4 `
        --sym `
        --group-size -1 `
        --ratio 1.0 `
        --trust-remote-code `
        $OutputDir

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Conversion failed. Check the output above." -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "✅ Conversion complete." -ForegroundColor Green
}

# ── Verify model loads on the requested device ────────────────────────────────
Write-Host ""
Write-Host "🔍 Verifying model loads on '$Device'..." -ForegroundColor Cyan

$verifyScript = @"
import sys
from pathlib import Path

try:
    import openvino_genai as ov_genai
except ImportError:
    print("WARN: openvino_genai not installed — skipping runtime verification.")
    print("      Install with:  uv add openvino-genai")
    sys.exit(0)

model_dir = Path(r'$($OutputDir -replace "\\", "/")')
if not model_dir.exists():
    print(f"ERROR: model directory not found: {model_dir}")
    sys.exit(1)

print(f"Loading pipeline from {model_dir} on $Device ...")
try:
    pipe = ov_genai.LLMPipeline(str(model_dir), "$Device")
    print("Model loaded. Running smoke-test inference...")
    result = pipe.generate("<|system|>\nYou are a security assistant.<|end|>\n<|user|>\nSay 'ok'<|end|>\n<|assistant|>\n", max_new_tokens=10)
    print(f"Response: {result}")
    print("SUCCESS: Model is functional.")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
"@

$verifyScript | python -
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Verification failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host " Model is ready at:" -ForegroundColor Green
Write-Host "   $OutputDir" -ForegroundColor White
Write-Host ""
Write-Host " Start the backend with:" -ForegroundColor Green
Write-Host "   cd services" -ForegroundColor White
Write-Host "   uv run uvicorn helios.main:app --reload" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
