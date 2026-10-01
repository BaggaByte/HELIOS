import asyncio
from typing import AsyncGenerator, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from helios.config import get_settings

settings = get_settings()

# SQLite doesn't support connection pool arguments — only pass them for PostgreSQL
_engine_kwargs: dict[str, Any] = {"echo": settings.DEBUG}
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    _engine_kwargs["max_overflow"] = 10

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    # Run Alembic migrations programmatically
    import logging
    from alembic.config import Config
    from alembic import command
    import pathlib
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get path to alembic.ini relative to this file (services/helios/infrastructure/database.py)
        # Assuming alembic.ini is in the services/ directory
        base_dir = pathlib.Path(__file__).parent.parent.parent
        
        import sys
        if getattr(sys, 'frozen', False):
            # When frozen with PyInstaller --onefile, files are extracted to sys._MEIPASS
            base_dir = pathlib.Path(sys._MEIPASS)
            
        alembic_ini_path = base_dir / "alembic.ini"
                
        if alembic_ini_path.exists():
            alembic_cfg = Config(str(alembic_ini_path))
            # Set the script_location explicitly so it works when running from anywhere
            alembic_cfg.set_main_option("script_location", str(base_dir / "alembic"))
            
            # Check if there is an existing database that has no alembic_version table
            async with engine.begin() as conn:
                def check_alembic(connection):
                    from sqlalchemy import inspect
                    inspector = inspect(connection)
                    tables = inspector.get_table_names()
                    # If users table exists but no alembic_version, we need to stamp it
                    if "users" in tables and "alembic_version" not in tables:
                        # Verify if all new tables from da139f94d0ef exist
                        new_tables = ["events", "knowledge_nodes", "project_files", "tasks", "knowledge_edges"]
                        if all(t in tables for t in new_tables):
                            return "da139f94d0ef" # It is already at the new schema
                        return "legacy" # Needs upgrade
                    return None
                
                db_state = await conn.run_sync(check_alembic)
                
            if db_state == "legacy":
                logger.info("Found legacy database. Creating backup before migration...")
                import shutil
                db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
                if db_path and pathlib.Path(db_path).exists():
                    shutil.copy2(db_path, f"{db_path}.legacy.bak")
                
                logger.info("Stamping with initial Alembic revision...")
                await asyncio.to_thread(command.stamp, alembic_cfg, "dfa9b81892d7")
            elif db_state == "da139f94d0ef":
                logger.info("Found unversioned but migrated database. Stamping with da139f94d0ef...")
                await asyncio.to_thread(command.stamp, alembic_cfg, "da139f94d0ef")
            
            # Run upgrade synchronously in a thread
            await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
            logger.info("Successfully applied database migrations.")
        else:
            logger.error(f"Could not find alembic.ini at {alembic_ini_path}. Migrations not applied.")
    except Exception as e:
        logger.error(f"Failed to apply database migrations: {e}")
        raise
