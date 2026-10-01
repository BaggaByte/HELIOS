"""
OpenVINO GenAI inference runtime.

Singleton wrapper around openvino_genai.LLMPipeline.
Falls back gracefully to a mock stream when:
  - openvino_genai is not installed
  - the model directory does not exist or contains no .xml file

Model path is resolved from settings (OV_MODEL_PATH), relative to the
services/ working directory where uvicorn is started from.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency — degrade gracefully
# ---------------------------------------------------------------------------
try:
    import openvino_genai as ov_genai  # type: ignore

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning(
        "openvino_genai not installed — runtime will operate in mock mode. "
        "Install with:  uv add openvino-genai"
    )


@dataclass
class GenerationConfig:
    max_new_tokens: int = 1024
    temperature: float = 0.1
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True


class OpenVINORuntime:
    """
    Singleton LLM inference manager.

    On first instantiation it loads the model from OV_MODEL_PATH.
    Subsequent instantiations return the already-initialised singleton.
    """

    _instance: Optional["OpenVINORuntime"] = None
    _initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> "OpenVINORuntime":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:  # type: ignore[attr-defined]
            return

        # Import settings lazily to avoid circular imports at module load time
        from helios.config import get_settings

        settings = get_settings()

        self.model_path: str = settings.OV_MODEL_PATH
        self.device: str = settings.OV_DEVICE
        self.pipeline: Any | None = None
        self._initialized = True

        model_dir = Path(self.model_path)

        if not model_dir.is_absolute():
            import sys

            if getattr(sys, "frozen", False):
                # If running as PyInstaller bundle, look next to the executable
                base_dir = Path(sys.executable).parent.parent
            else:
                # If running from source, assume services/ is the base
                base_dir = Path.cwd()
            model_dir = base_dir / model_dir

        if model_dir.exists() and any(model_dir.glob("*.xml")):
            logger.info(f"Model directory found at {model_dir} — loading...")
            self._load_pipeline(model_dir)
        else:
            logger.warning(
                f"Model not found at '{model_dir}'. "
                "Runtime operating in mock mode. "
                "Run  scripts/download_model.ps1  to download the model."
            )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _load_pipeline(self, model_dir: Path) -> None:
        if not GENAI_AVAILABLE:
            logger.error(
                "openvino_genai is not installed — cannot load model. "
                "Install with:  uv add openvino-genai"
            )
            return

        try:
            from openvino import Core  # type: ignore

            core = Core()
            available_devices = core.available_devices
        except Exception as exc:
            logger.error(f"Failed to query OpenVINO devices: {exc}")
            available_devices = []

        # Device preference: honour config, fall back gracefully
        preference_map: dict[str, list[str]] = {
            "NPU": ["NPU", "GPU", "CPU"],
            "GPU": ["GPU", "CPU"],
            "AUTO": ["AUTO"],  # AUTO is its own meta-device
            "CPU": ["CPU"],
        }
        preferred = preference_map.get(self.device, ["AUTO"])

        selected = "CPU"
        for dev in preferred:
            if dev == "AUTO" or dev in available_devices:
                selected = dev
                break

        self.device = selected
        logger.info(
            f"Loading OpenVINO GenAI pipeline from '{model_dir}' on {selected}..."
        )

        try:
            self.pipeline = ov_genai.LLMPipeline(str(model_dir), selected)
            logger.info(f"✅ Model loaded successfully on {selected}")
        except Exception as exc:
            logger.error(f"Failed to load model: {exc}")
            self.pipeline = None

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    @classmethod
    def is_npu_available(cls) -> bool:
        try:
            from openvino import Core  # type: ignore

            return "NPU" in Core().available_devices
        except Exception:
            return False

    def reload(self) -> None:
        """Force a model reload (e.g. after updating OV_MODEL_PATH at runtime)."""
        self.pipeline = None
        self._initialized = False
        self.__init__()

    async def generate_stream(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream generated tokens for *prompt*.

        If the model is not loaded, a mock stream is returned so the rest of
        the application stays functional during development.
        """
        if config is None:
            config = GenerationConfig()

        if self.pipeline is None or not GENAI_AVAILABLE:
            logger.debug("Mock stream — model not loaded.")
            mock = [
                "*(HELIOS is running in mock mode — no model loaded)*\n\n",
                "I received your message:\n\n> ",
                prompt[:200],
                "\n\nTo enable real inference, download the model with:\n",
                "```\npowershell scripts/download_model.ps1\n```",
            ]
            for chunk in mock:
                yield chunk
                await asyncio.sleep(0.04)
            return

        token_queue: asyncio.Queue[str | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _streamer_callback(token_text: str) -> bool:
            """Called synchronously by OpenVINO in the inference thread."""
            # Phi-3-mini stop tokens
            stop_tokens = ("<|end|>", "<|endoftext|>", "<|user|>", "<|system|>")
            for tok in stop_tokens:
                if tok in token_text:
                    clean = token_text
                    for t in stop_tokens:
                        clean = clean.replace(t, "")
                    if clean:
                        loop.call_soon_threadsafe(token_queue.put_nowait, clean)
                    loop.call_soon_threadsafe(token_queue.put_nowait, None)
                    return True  # signal stop to pipeline
            loop.call_soon_threadsafe(token_queue.put_nowait, token_text)
            return False

        def _run_inference() -> None:
            try:
                gen_cfg = self.pipeline.get_generation_config()
                gen_cfg.max_new_tokens = config.max_new_tokens
                gen_cfg.temperature = config.temperature
                gen_cfg.top_p = config.top_p
                gen_cfg.top_k = config.top_k
                gen_cfg.repetition_penalty = config.repetition_penalty
                gen_cfg.do_sample = config.do_sample
                self.pipeline.generate(prompt, gen_cfg, _streamer_callback)
            except Exception as exc:
                logger.error(f"Inference error: {exc}")
            finally:
                loop.call_soon_threadsafe(token_queue.put_nowait, None)

        inference_task = loop.run_in_executor(None, _run_inference)

        while True:
            token = await token_queue.get()
            if token is None:
                break
            yield token

        await inference_task

    def get_status(self) -> dict[str, Any]:
        return {
            "device": self.device,
            "model_path": self.model_path,
            "loaded": self.pipeline is not None,
            "npu_available": self.is_npu_available(),
            "genai_installed": GENAI_AVAILABLE,
        }
