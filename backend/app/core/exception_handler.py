from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.schemas.base import ResponseModel

from app.core.exception import CustomException
from app.core.logging import get_logger


logger = get_logger("app")


# Custom Exception handler
async def custom_exception_handler(_: Request, exc: CustomException):
    # logger.error(exc, exc_info=True)
    print(exc.__class__.__name__, exc.status)
    return JSONResponse(
        status_code=exc.status,
        content={
            "status": exc.status,
            "message": exc.message,
            "data": exc.data,
        },
    )


async def global_exception_handler(_: Request, exc: Exception):
    # logger.error(exc, exc_info=True)
    print(exc.__class__.__name__)
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "message": "서버에서 처리 중 알 수 없는 오류가 발생했습니다.",
            "data": str(exc),
        },
    )
