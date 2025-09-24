from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.database.models.base import Base
from app.core.logging import get_logger

logger = get_logger("app")

DATABASE_URL = settings.database_url

async_engine = create_async_engine(
    DATABASE_URL,
    echo=(settings.log_level.lower() in ["debug", "trace"]),
    pool_size=settings.db_pool_size,  # 커넥션 풀 크기
    max_overflow=settings.db_max_overflow,  # 최대 초과 커넥션 수
    pool_timeout=settings.db_pool_timeout,  # 커넥션 풀에서 기다리는 최대 시간
    pool_recycle=settings.db_pool_recycle,  # 커넥션 재사용 시간
    pool_pre_ping=settings.db_pool_pre_ping,  # 사용 전 연결 상태 확인
)

SessionLocal = sessionmaker(
    bind=async_engine,
    autocommit=False,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def create_tables():
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.info(f"Error creating tables: {e}")


async def drop_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# 비동기 트랜잭션 매니저 추가
@asynccontextmanager
async def async_transaction(session: AsyncSession) -> AsyncGenerator:
    """비동기 트랜잭션 컨텍스트 매니저"""
    async with session.begin():
        try:
            yield
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
