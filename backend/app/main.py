from contextlib import asynccontextmanager

from uuid import uuid4
from time import time

from app.core.config import settings
from app.api.v1 import router as v1_router
from app.core.db import create_tables
from app.core.exception import CustomException
from app.core.exception_handler import (
    custom_exception_handler,
    global_exception_handler,
)
from app.core.logging import setup_logger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = setup_logger()


# lifespan 이벤트 핸들러 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 테이블 생성
    # 테이블 이미 존재하는 경우 아무 작업도 수행하지 않음
    await create_tables()
    yield
    # await drop_tables()
    # 서버 종료 시 실행할 작업 (필요 시 추가 가능)


def create_app() -> FastAPI:
    """
    FastAPI 애플리케이션 생성 함수
    """
    app = FastAPI(
        lifespan=lifespan,
        title="AI-Agent-MVP-BE",
        description="AI-Agent-MVP-BE API V1",
        version="1.0.0",  # API 버전
        root_path=settings.root_path,
        openapi_url=settings.openapi_url,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
    )

    origins = [
        "http://localhost:3000",
        "https://localhost:3000",
        "http://localhost:8000",
        "https://localhost:8000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def handle_request(request: Request, call_next):
        # 요청 시작 시간 로깅
        start_time = time()

        # Request ID/path logging, request_id가 없으면 새로 생성
        request_id = request.headers.get("X-Request-ID", uuid4())
        request.state.request_id = request_id
        logger.info(
            (
                f"[{request_id}] {request.method} "
                f"{request.url.path} Start request."
            )
        )
        response = await call_next(request)
        # 요청 종료 시간 로깅
        end_time = time()
        logger.info(
            (
                f"[{request_id}] {request.url.path} End request."
                f" Elapsed time: {end_time - start_time:.2f}s"
            )
        )
        return response

    # add routers
    app.include_router(v1_router)

    # 커스텀 예외 핸들러 등록
    app.add_exception_handler(
        CustomException,
        custom_exception_handler,  # pyright: ignore[reportArgumentType]
    )
    # 기본 예외 핸들러 등록
    app.add_exception_handler(
        Exception,
        global_exception_handler,  # pyright: ignore[reportArgumentType]
    )

    return app


# 전역 앱 인스턴스
app = create_app()
