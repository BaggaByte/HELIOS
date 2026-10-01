import asyncio
import argparse
import getpass
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from helios.config import get_settings
from helios.infrastructure.database import init_db
from helios.models.project import Project
from helios.models.user import User
from helios.api.v1.auth import get_password_hash, LEGACY_SYSTEM_USER_IDS


async def seed(password: str, scope: str = ""):
    settings = get_settings()
    await init_db()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check/create user
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalars().first()

        if not user:
            user = User(
                username="admin",
                password_hash=get_password_hash(password),
                role="admin",
            )
            session.add(user)
            await session.commit()
            print("✅ Admin user created successfully.")
        else:
            print(
                "⚠️ Admin user already exists. If you want to change the password, you must do so via the UI or DB update."
            )

        # Check/create project
        result = await session.execute(
            select(Project).where(Project.id == "default-project-id")
        )
        project = result.scalars().first()
        if not project:
            # We must determine a scope
            project_scope = scope
            if not project_scope:
                project_scope = input(
                    "Enter scope for the Default Workspace (e.g. 192.168.1.0/24 or example.com): "
                ).strip()
                if not project_scope:
                    print("❌ Scope is required. Aborting.")
                    exit(1)

            project = Project(
                id="default-project-id",
                name="Default Workspace",
                scope=project_scope,
                status="active",
                created_by=user.id,
            )
            session.add(project)
            await session.commit()
            print(f"✅ Default project created with scope: {project_scope}")
        else:
            print("✅ Default project already exists.")

        # Claim orphaned projects
        result = await session.execute(
            select(Project).where(Project.created_by.in_(LEGACY_SYSTEM_USER_IDS))
        )
        orphaned = result.scalars().all()
        if orphaned:
            for p in orphaned:
                # If they were assigned to system_user or are otherwise orphaned, assign to admin
                p.created_by = user.id
            await session.commit()
            print(
                f"✅ Claimed {len(orphaned)} legacy/orphaned projects for the admin user."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bootstrap the HELIOS database with an initial admin user and default project."
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Admin password (if not provided, will prompt interactively)",
    )
    parser.add_argument(
        "--scope",
        type=str,
        help="Default project scope (if not provided, will prompt interactively)",
    )
    args = parser.parse_args()

    password = args.password
    if not password:
        password = getpass.getpass("Enter password for the initial 'admin' user: ")
        if not password:
            print("❌ Password cannot be empty.")
            exit(1)

    asyncio.run(seed(password, args.scope))
