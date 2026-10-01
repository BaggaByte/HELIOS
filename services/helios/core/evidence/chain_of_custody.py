import hashlib
import json
import logging
import os
import time
from typing import Any

from filelock import FileLock

logger = logging.getLogger(__name__)


class ChainOfCustody:
    """
    Maintains a tamper-evident append-only ledger of evidence.
    Each entry is hashed and linked to the previous entry. Note that while this
    prevents stealthy modification of historical records, it is only truly
    immutable if externally anchored or cryptographically signed by a trusted hardware module.
    """

    def __init__(
        self,
        ledger_path: str = "data/evidence_ledger.jsonl",
        create_if_missing: bool = True,
    ):
        self.ledger_path = ledger_path
        self.lock_path = self.ledger_path + ".lock"
        if create_if_missing:
            os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
            # We only create genesis if it truly doesn't exist.
            with FileLock(self.lock_path):
                self._ensure_ledger_exists()

    def _ensure_ledger_exists(self):
        if (
            not os.path.exists(self.ledger_path)
            or os.path.getsize(self.ledger_path) == 0
        ):
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                # Genesis block
                genesis = {
                    "id": "genesis",
                    "timestamp": time.time(),
                    "action": "INIT",
                    "previous_hash": "0" * 64,
                }
                genesis["hash"] = self._compute_hash(genesis)
                f.write(json.dumps(genesis) + "\n")

    def _compute_hash(self, record: dict[str, Any]) -> str:
        # Create a copy without the hash field to compute the hash
        record_copy = {k: v for k, v in record.items() if k != "hash"}
        # Deterministic JSON serialization
        serialized = json.dumps(record_copy, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _get_last_record(self) -> dict[str, Any]:
        last_line = None
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line

        if last_line:
            return json.loads(last_line)
        raise ValueError("Ledger is corrupted or empty.")

    def log_evidence(
        self,
        evidence_id: str,
        action: str,
        details: dict[str, Any],
        user: str = "system",
    ) -> dict[str, Any]:
        """
        Logs an action performed on an evidence item safely under concurrency.
        """
        with FileLock(self.lock_path):
            last_record = self._get_last_record()

            record = {
                "id": evidence_id,
                "timestamp": time.time(),
                "action": action,
                "user": user,
                "details": details,
                "previous_hash": last_record["hash"],
            }

            record["hash"] = self._compute_hash(record)

            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

        logger.info(f"Evidence {evidence_id} logged: {action}")
        return record

    def get_evidence_events(self, evidence_id: str) -> list[dict[str, Any]]:
        """
        Returns all ledger events for a specific evidence_id.
        """
        events = []
        if not os.path.exists(self.ledger_path):
            return events

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("id") == evidence_id:
                    events.append(record)
        return events

    def verify_ledger(self) -> bool:
        """
        Verifies the integrity of the entire ledger by checking hash chains.
        """
        previous_hash = "0" * 64
        is_genesis = True

        if not os.path.exists(self.ledger_path):
            return False  # A missing ledger cannot be verified as valid

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)

                # Check previous hash
                if not is_genesis and record["previous_hash"] != previous_hash:
                    logger.error(f"Chain broken at record: {record.get('id')}")
                    return False

                # Check current hash
                expected_hash = self._compute_hash(record)
                if record["hash"] != expected_hash:
                    logger.error(f"Hash mismatch at record: {record.get('id')}")
                    return False

                previous_hash = record["hash"]
                is_genesis = False

        if is_genesis:
            return False  # Empty ledger (not even genesis) is invalid

        return True
