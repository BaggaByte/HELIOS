"""
Celery application factory for HELIOS background task processing.

Provides a real Celery instance backed by Redis when the broker is reachable,
and falls back to a lightweight synchronous stub otherwise — so the API
server starts and all tasks still execute (sequentially, in-process) even
without Redis installed, which preserves the offline / local-first guarantees.

Environment variables (via .env):
    CELERY_BROKER_URL  – Redis broker URL  (default: redis://localhost:6379/1)
    REDIS_URL          – Redis result backend (default: redis://localhost:6379/0)

To run a real Celery worker:
    cd services
    uv run celery -A helios.infrastructure.celery_app.celery_app worker \
        --loglevel=info --concurrency=2 -Q helios
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import real Celery
# ---------------------------------------------------------------------------
try:
    from celery import Celery as _Celery  # type: ignore

    _CELERY_AVAILABLE = True
except ImportError:
    _CELERY_AVAILABLE = False
    logger.warning(
        "celery package not installed — background tasks will run synchronously. "
        "Install with:  uv add celery redis"
    )


# ---------------------------------------------------------------------------
# Synchronous fallback stub (no Redis required)
# ---------------------------------------------------------------------------
class _SyncTaskResult:
    """Mimics the subset of AsyncResult that callers actually use."""

    def __init__(self, return_value: Any) -> None:
        self.id = "sync-task"
        self.result = return_value
        self.status = "SUCCESS"

    def get(self, timeout: float | None = None) -> Any:  # noqa: ARG002
        return self.result


class _SyncCeleryApp:
    """
    Lightweight in-process stub that runs tasks synchronously in the calling
    thread.  All tasks decorated with @celery_app.task still work identically
    to their real counterparts — callers can use .delay() or call directly.
    """

    def __init__(self, name: str, broker: str, backend: str) -> None:
        self.name = name
        self.broker = broker
        self.backend = backend
        logger.info(
            "HELIOS running with synchronous task fallback "
            f"(broker={broker!r} unreachable or celery not installed). "
            "Start Redis and install celery to enable async task execution."
        )

    def task(self, *args: Any, **kwargs: Any) -> Callable:
        """Decorator that attaches a .delay() shim to any callable."""

        def decorator(func: Callable) -> Callable:
            def delay(*task_args: Any, **task_kwargs: Any) -> _SyncTaskResult:
                logger.info(
                    f"[sync-task] Executing '{func.__name__}' synchronously "
                    "(no Redis broker available)."
                )
                rv = func(*task_args, **task_kwargs)
                return _SyncTaskResult(rv)

            func.delay = delay  # type: ignore[attr-defined]
            func.apply_async = lambda args=(), kwargs={}, **_: _SyncTaskResult(  # type: ignore[attr-defined]
                func(*args, **kwargs)
            )
            return func

        # Support both @celery_app.task and @celery_app.task(bind=True, ...)
        if len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        return decorator

    # Stub out the most-used Celery app attributes so type-checked code
    # that reads celery_app.conf etc. doesn't raise AttributeError.
    class _Conf:
        def update(self, **_: Any) -> None:
            pass

    conf = _Conf()


# ---------------------------------------------------------------------------
# Real Celery factory
# ---------------------------------------------------------------------------
def _make_real_celery(broker_url: str, backend_url: str) -> Any:
    app = _Celery(
        "helios",
        broker=broker_url,
        backend=backend_url,
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_acks_late=True,  # re-queue on worker crash
        worker_prefetch_multiplier=1,  # fair dispatch for long scans
        broker_connection_retry_on_startup=True,
        result_expires=3600,  # clean up results after 1 hour
        task_default_queue="helios",
        task_routes={
            "helios.tasks.*": {"queue": "helios"},
        },
    )
    return app


# ---------------------------------------------------------------------------
# Module-level singleton — prefer real Celery, fall back to sync stub
# ---------------------------------------------------------------------------
def _build_celery_app():
    # Import lazily to avoid circular imports at module load time
    try:
        from helios.config import get_settings

        settings = get_settings()
        broker_url = settings.CELERY_BROKER_URL
        backend_url = settings.REDIS_URL
    except Exception:
        broker_url = "redis://localhost:6379/1"
        backend_url = "redis://localhost:6379/0"

    if not _CELERY_AVAILABLE:
        return _SyncCeleryApp("helios", broker=broker_url, backend=backend_url)

    # Probe whether the broker is actually reachable before committing.
    # A quick connection attempt at startup is better than silently blocking
    # every task call later.
    try:
        import redis as _redis  # type: ignore
        from urllib.parse import urlparse

        parsed = urlparse(broker_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        db_index = int((parsed.path or "/1").lstrip("/") or "1")
        r = _redis.Redis(host=host, port=port, db=db_index, socket_connect_timeout=1)
        r.ping()
        logger.info(f"✅ Redis broker reachable at {broker_url} — using real Celery.")
        return _make_real_celery(broker_url, backend_url)
    except Exception as exc:
        logger.warning(
            f"Redis broker at {broker_url!r} is unreachable ({exc}). "
            "Falling back to synchronous task execution. "
            "Start Redis to enable async background scans."
        )
        return _SyncCeleryApp("helios", broker=broker_url, backend=backend_url)


celery_app = _build_celery_app()
