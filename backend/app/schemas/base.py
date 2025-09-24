from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from app.schemas.pagination import Pagination

T = TypeVar("T")


# 기본 응답 모델
class ResponseModel(BaseModel, Generic[T]):
    status: int = 200
    message: str = "success"
    pagination: Optional[Pagination] = None
    data: Optional[T] = None
