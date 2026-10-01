import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from helios.core.project_memory.retriever import build_memory_context_prompt
from helios.infrastructure.openvino_runtime import GenerationConfig, OpenVINORuntime
from helios.infrastructure.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str


class ChatEngine:
    def __init__(self):
        self.ai_runtime = OpenVINORuntime()
        self.vector_store = None

        try:
            self.vector_store = VectorStore()
            logger.info("VectorStore initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")

    def _build_system_prompt(self, memory_context: str) -> str:
        return (
            "You are HELIOS, an AI-powered offensive security copilot. "
            "CRITICAL OPERATIONAL RULES:\n"
            "1. NO HALLUCINATIONS: Do not invent YARA hits, signatures, suspicious imports, packing routines, or network behavior not explicitly provided in the context.\n"
            "2. HASH HANDLING: MD5 and SHA256 hashes generated for the same file belong to the exact same file (different hash algorithms naturally produce different outputs). Never claim hash inconsistency when MD5 and SHA256 are both supplied for a file.\n"
            "3. STATIC ANALYSIS ACCURACY:\n"
            "   - Entropy < 6.0 is low and normal for unstripped code/data sections. Only entropy > 7.0 suggests packing or encryption.\n"
            "   - If imports are standard libc (e.g., printf, malloc, free), explicitly mark them as standard benign libc calls. Do not speculate about packers or exploit kits.\n"
            "   - Respect binary format (ELF vs PE). Never recommend Windows tools (x64dbg, OllyDbg) for Linux ELF binaries.\n"
            "   - Calibrate risk recommendations: Do not recommend full malware-sandbox treatment (QEMU, Wireshark) for a small, benign test binary.\n"
            "4. OBJECTIVE AND CLINICAL TONE: If static analysis shows no indicators of malice, state clearly and concisely that the binary is benign.\n\n"
            "You are currently analyzing a penetration testing project.\n\n"
            f"{memory_context}"
        )

    def _build_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        history: list[ChatMessage] | None = None,
    ) -> str:
        """
        Build a prompt using Phi-3's native chat template.

        Phi-3-mini uses special tokens:
            <|system|>   ... <|end|>
            <|user|>     ... <|end|>
            <|assistant|>... <|end|>

        We keep the last 6 history turns (3 user+assistant pairs) to stay
        well within the 4096-token context limit at INT4.
        """
        parts: list[str] = []

        # System block
        parts.append(f"<|system|>\n{system_prompt}<|end|>\n")

        # History — cap at 6 turns to avoid context overflow
        if history:
            for msg in history[-6:]:
                role_token = "<|user|>" if msg.role == "user" else "<|assistant|>"
                parts.append(f"{role_token}\n{msg.content}<|end|>\n")

        # Current user message, optionally prefixed with retrieved context
        user_content = user_prompt
        if context:
            user_content = (
                f"Relevant context from knowledge base:\n{context}\n\n"
                f"---\n\n{user_prompt}"
            )

        parts.append(f"<|user|>\n{user_content}<|end|>\n")
        parts.append("<|assistant|>\n")

        return "".join(parts)

    async def generate_response(
        self,
        prompt: str,
        history: list[ChatMessage] | None = None,
        recon_context: str = "",
        project_id: str = "",
        gen_config: GenerationConfig | None = None,
    ) -> AsyncGenerator[str]:

        start_time = time.time()

        # 1. Context Injection (RAG & Recon)
        context_str = ""

        if recon_context:
            context_str += f"## Active Reconnaissance Data:\n{recon_context}\n\n"

        if self.vector_store and project_id:
            try:
                results = self.vector_store.search_findings(
                    query=prompt, n_results=3, project_id=project_id
                )
                if results and "documents" in results and results["documents"]:
                    found_docs = results["documents"][0]
                    if found_docs:
                        cleaned_docs = [
                            doc.strip() for doc in found_docs if doc.strip()
                        ]
                        if cleaned_docs:
                            context_str += "## Relevant Knowledge Base Findings:\n"
                            context_str += "\n---\n".join(cleaned_docs)
                            logger.debug(
                                f"Retrieved {len(cleaned_docs)} context chunks."
                            )
            except Exception as e:
                logger.warning(
                    f"Vector search failed, proceeding without vector context: {e}"
                )

        # 2. Build Augmented Prompt
        memory_context = build_memory_context_prompt(project_id) if project_id else ""
        system_prompt = self._build_system_prompt(memory_context)
        augmented_prompt = self._build_prompt(
            system_prompt, prompt, context_str.strip(), history
        )

        logger.info(
            f"Generated prompt in {(time.time() - start_time) * 1000:.2f}ms. Starting inference..."
        )

        # 3. Stream Generation
        tokens_generated = 0
        first_token_time = None

        async for token in self.ai_runtime.generate_stream(
            augmented_prompt, gen_config
        ):
            if first_token_time is None:
                first_token_time = time.time()
                logger.info(
                    f"Time to first token (TTFT): {(first_token_time - start_time) * 1000:.2f}ms"
                )

            tokens_generated += 1
            yield token

        logger.info(f"Generation complete. Total tokens: {tokens_generated}")

    def get_status(self) -> dict[str, Any]:
        return {
            "engine": "ready",
            "vector_store_active": self.vector_store is not None,
            "runtime_status": self.ai_runtime.get_status(),
        }
