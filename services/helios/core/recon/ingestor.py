import logging
from collections.abc import Callable
from typing import Any

from helios.core.recon.analyzer import analyzer
from helios.core.recon.prioritizer import prioritizer

logger = logging.getLogger(__name__)


class ReconIngestor:
    """
    Generic ingestor that accepts raw file content, routes it to the correct parser,
    analyzes the attack surface, assigns risk, and prepares it for DB insertion.
    """

    def __init__(self):
        self._parsers: dict[str, Callable] = {}

    def register_parser(self, tool_name: str, parser_func: Callable):
        """Register a specific parser function for a tool."""
        self._parsers[tool_name.lower()] = parser_func

    def ingest(self, tool_name: str, raw_content: str) -> dict[str, Any]:
        """
        Routes the raw content to the registered parser.
        """
        tool_name = tool_name.lower()
        if tool_name not in self._parsers:
            raise ValueError(f"No parser registered for tool '{tool_name}'")

        parser_func = self._parsers[tool_name]

        try:
            parsed_data = parser_func(raw_content)
        except Exception as e:
            logger.error(f"Parser {tool_name} failed: {e}")
            raise ValueError(f"Failed to parse {tool_name} output: {e}")

        # Optional: Pipeline data through analyzer and prioritizer
        # In a real pipeline, we'd iterate through hosts/endpoints and enrich them
        if "hosts" in parsed_data:
            for host in parsed_data["hosts"]:
                attack_surface = analyzer.analyze_host(host)
                risk = prioritizer.calculate_risk(host, attack_surface)
                host["_enriched"] = {"attack_surface": attack_surface, "risk": risk}

        return parsed_data


ingestor = ReconIngestor()
