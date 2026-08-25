import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from helios.config import get_settings
settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
from helios.models.project import Project
from sqlalchemy import select

async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(Project).where(Project.id == "default-project-id"))
        project = result.scalars().first()
        if not project:
            project = Project(id="default-project-id", name="Default Workspace", scope="*", status="active")
            session.add(project)
            await session.commit()
            print("Project seeded")
        else:
            print("Project already exists")

if __name__ == "__main__":
    asyncio.run(seed())
