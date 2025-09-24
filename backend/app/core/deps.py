from app.core.db import SessionLocal
from app.core.config import settings
from langchain_openai import ChatOpenAI


async def get_db():
    db = SessionLocal()
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()


def get_llm() -> ChatOpenAI:
    """OpenAI LLM 인스턴스를 반환하는 의존성 함수"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=None,
        max_retries=2,
        api_key=settings.openai_secret_key,
    )
