import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common import descriptions_and_images_for_categories, descriptions_and_images_for_banners
from app.database.models import Base
from app.database import requests as rq

engine = create_async_engine(url=os.getenv("DB_URL"), echo=True)

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await rq.orm_create_categories(session, descriptions_and_images_for_categories)
        await rq.orm_add_banner(session, descriptions_and_images_for_banners)

async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
