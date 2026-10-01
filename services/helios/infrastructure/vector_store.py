"""
VectorStore — ChromaDB wrapper with at-rest content encryption.

Files uploaded to HELIOS are stored encrypted on disk (via StorageManager +
EncryptionManager). This wrapper extends that protection to the ChromaDB
documents collection so that uploaded file content is never persisted as
plaintext inside the Chroma SQLite/parquet store.

How it works
────────────
• `add_finding()` / `add_document()` manually generate embeddings from the
  plaintext before encryption, and store only the encrypted document in ChromaDB.

• `search_findings()` / `search_documents()` decrypt retrieved documents
  before returning them to callers, so the LLM receives readable context.

• The embedding is generated from the plaintext before encryption.
  To preserve semantic search, we pass the **plaintext** as the query text
  but store the **ciphertext** as the document — Chroma embeds the
  plaintext query and matches it against the vectors generated from the
  plaintext document (embedded when `add` was called).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from helios.config import get_settings

logger = logging.getLogger(__name__)


def _try_load_encryption() -> Any:
    """Return an EncryptionManager instance. Fails closed if unavailable."""
    try:
        from helios.infrastructure.encryption import EncryptionManager

        return EncryptionManager()
    except Exception as exc:
        logger.error(
            f"VectorStore: EncryptionManager unavailable ({exc}). "
            "Failing closed to prevent plaintext storage."
        )
        raise RuntimeError("VectorStore cannot operate without encryption.") from exc


class VectorStore:
    def __init__(self, persist_dir: str | None = None):
        settings = get_settings()
        self.persist_dir = Path(persist_dir or settings.CHROMA_PERSIST_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

        self.findings_collection = self.client.get_or_create_collection(
            name="findings",
            metadata={"description": "Security findings and vulnerabilities"},
        )

        self.docs_collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Parsed logs and documents"},
        )

        # Encryption is required.
        self._enc = _try_load_encryption()
        logger.info("VectorStore initialized with at-rest encryption enabled.")

    # ── Encryption helpers ────────────────────────────────────────────────────

    def _encrypt(self, text: str) -> str:
        """Encrypt text for storage; returns ciphertext as a UTF-8 string."""
        if self._enc is None:
            raise RuntimeError("EncryptionManager is missing.")
        try:
            return self._enc.encrypt_data(text.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            logger.error(f"VectorStore: encrypt failed ({exc}).")
            raise

    def _decrypt(self, stored: str) -> str:
        """Decrypt stored text; returns plaintext."""
        if self._enc is None:
            raise RuntimeError("EncryptionManager is missing.")
        # Fail closed on unexpected plaintext (Fernet tokens always start with gAAAAA)
        if not stored.startswith("gAAAAA"):
            logger.error(
                "VectorStore: Found unencrypted data in store. Migration required."
            )
            raise ValueError("Unexpected plaintext record found in vector store.")
        try:
            return self._enc.decrypt_data(stored.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            logger.error(f"VectorStore: decrypt failed ({exc}).")
            raise

    def _decrypt_results(self, results: dict[str, Any]) -> dict[str, Any]:
        """Decrypt all document strings in a ChromaDB query result dict."""
        if not results or "documents" not in results:
            return results
        decrypted_docs: list[list[str]] = []
        for doc_group in results["documents"]:
            decrypted_docs.append([self._decrypt(doc) for doc in doc_group])
        return {**results, "documents": decrypted_docs}

    # ── Public API ────────────────────────────────────────────────────────────

    def add_finding(self, id: str, text: str, metadata: dict | None = None) -> None:
        """
        Add a finding to the vector store.
        The embedding is generated from *plaintext*; stored document is *encrypted*.
        """
        try:
            # Manually embed the plaintext first
            ef = getattr(
                self.findings_collection, "_embedding_function", None
            ) or getattr(self.findings_collection, "embedding_function", None)
            if not ef:
                raise RuntimeError("No embedding function found on collection")

            embeddings = ef([text])
            ciphertext = self._encrypt(text)

            self.findings_collection.add(
                documents=[ciphertext],
                embeddings=embeddings,
                metadatas=[metadata or {}],
                ids=[id],
            )
        except Exception as exc:
            logger.error(f"VectorStore.add_finding failed: {exc}", exc_info=True)
            raise

    def add_document(self, id: str, text: str, metadata: dict | None = None) -> None:
        """Add a parsed document to the docs collection (encrypted at rest)."""
        try:
            ef = getattr(self.docs_collection, "_embedding_function", None) or getattr(
                self.docs_collection, "embedding_function", None
            )
            if not ef:
                raise RuntimeError("No embedding function found on collection")

            embeddings = ef([text])
            ciphertext = self._encrypt(text)

            self.docs_collection.add(
                documents=[ciphertext],
                embeddings=embeddings,
                metadatas=[metadata or {}],
                ids=[id],
            )
        except Exception as exc:
            logger.error(f"VectorStore.add_document failed: {exc}", exc_info=True)
            raise

    def search_findings(
        self,
        query: str,
        n_results: int = 3,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Search for similar findings; returns decrypted documents.
        `query` is always plaintext — Chroma embeds it and matches against
        the vectors that were generated from plaintext at add-time.
        """
        query_args: dict[str, Any] = {"query_texts": [query], "n_results": n_results}
        if project_id:
            query_args["where"] = {"project_id": project_id}
        results = self.findings_collection.query(**query_args)
        return self._decrypt_results(results)

    def search_documents(
        self,
        query: str,
        n_results: int = 3,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Search for similar documents; returns decrypted documents."""
        query_args: dict[str, Any] = {"query_texts": [query], "n_results": n_results}
        if project_id:
            query_args["where"] = {"project_id": project_id}
        results = self.docs_collection.query(**query_args)
        return self._decrypt_results(results)

    def delete_finding(self, id: str) -> None:
        """Remove a finding by ID."""
        try:
            self.findings_collection.delete(ids=[id])
        except Exception as exc:
            logger.warning(f"VectorStore.delete_finding({id}) failed: {exc}")
