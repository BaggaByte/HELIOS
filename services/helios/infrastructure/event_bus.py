import logging
import asyncio
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)

# MVP Scaffold: In-memory Event Bus for local-first operations without Redis Pub/Sub
class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        logger.info("Initialized local in-memory Event Bus")

    async def publish(self, channel: str, message: Any):
        """Publish a message to a channel."""
        logger.debug(f"EventBus Publish [{channel}]: {message}")
        if channel in self._subscribers:
            for callback in self._subscribers[channel]:
                # Fire and forget callback execution
                asyncio.create_task(self._safe_execute(callback, message))

    def subscribe(self, channel: str, callback: Callable):
        """Subscribe a callback to a channel."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)
        logger.debug(f"EventBus Subscribed to [{channel}]")

    async def _safe_execute(self, callback: Callable, message: Any):
        """Safely execute the callback and catch any errors."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
        except Exception as e:
            logger.error(f"EventBus Callback Error: {e}")

event_bus = EventBus()
