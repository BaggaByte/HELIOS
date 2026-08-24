import os
import chromadb
from chromadb.config import Settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_dir: str = "data/vector_db"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # We will store different types of data in different collections
        self.findings_collection = self.client.get_or_create_collection(
            name="findings",
            metadata={"description": "Security findings and vulnerabilities"}
        )
        
        self.docs_collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Parsed logs and documents"}
        )
        logger.info("Vector Store initialized")
        
    def add_finding(self, id: str, text: str, metadata: dict = None):
        """Adds a finding to the vector store"""
        self.findings_collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[id]
        )
        
    def search_findings(self, query: str, n_results: int = 3):
        """Searches for similar findings"""
        results = self.findings_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
