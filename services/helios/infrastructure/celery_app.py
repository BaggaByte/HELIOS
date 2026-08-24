import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# MVP Scaffold: Mocking Celery for local-first operations without Redis
class MockCeleryApp:
    def __init__(self, name: str, broker: str):
        self.name = name
        self.broker = broker
        logger.info(f"Initialized Mock Celery App '{name}' with broker '{broker}'")
        
    def task(self, *args, **kwargs):
        """Mock decorator for celery tasks."""
        def decorator(func: Callable) -> Callable:
            # Attach a delay method to mock async execution
            def delay(*task_args, **task_kwargs):
                logger.info(f"Mock Celery: Executing task '{func.__name__}' synchronously.")
                return func(*task_args, **task_kwargs)
            func.delay = delay
            return func
        return decorator

# In a production environment, this would be:
# from celery import Celery
# celery_app = Celery("helios", broker=settings.CELERY_BROKER_URL)
celery_app = MockCeleryApp("helios", broker="mock://redis")
