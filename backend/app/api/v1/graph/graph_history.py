from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    Path,
    Body,
    status as http_status,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4

from app.core.deps import get_db
from app.core.exception import InternalServerError, CustomException
from app.schemas.base import ResponseModel
from app.schemas.graph.graph_history import (
    GraphHistoryCreateRequest,
    GraphHistoryUpdateRequest,
    GraphHistoryDeleteRequest,
)
from app.services.graph import graph_history as graph_history_service
from app.core.logging import get_logger

logger = get_logger("app")

router = APIRouter()


# 그래프 히스토리 목록 조회
@router.get("", response_model=ResponseModel)
async def get_graph_history_list(
    request: Request,
    response: Response,
    page: int = Query(0, ge=0, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    graph_history_id: Optional[UUID4] = Query(
        None, description="그래프 히스토리 ID(Filter)"
    ),
    graph_id: Optional[UUID4] = Query(None, description="그래프 ID(Filter)"),
    status: Optional[str] = Query(None, description="상태(Filter)"),
    db: AsyncSession = Depends(get_db),
):
    """
    그래프 히스토리 목록 조회 API
    """
    try:
        pagination, response_data = (
            await graph_history_service.get_graph_histories(
                db=db,
                page=page,
                size=size,
                graph_history_id=graph_history_id,
                graph_id=graph_id,
                status=status,
            )
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 히스토리 목록 조회에 성공했습니다.",
            pagination=pagination,
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="그래프 히스토리 목록 조회에 실패했습니다.",
            data=str(e),
        )


# 그래프 히스토리 상세 조회
@router.get("/{graph_history_id}", response_model=ResponseModel)
async def get_graph_history(
    request: Request,
    response: Response,
    graph_history_id: UUID4 = Path(..., description="그래프 히스토리 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    그래프 히스토리 상세 조회 API
    """
    try:
        response_data = await graph_history_service.get_graph_history(
            db=db,
            graph_history_id=graph_history_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 히스토리 상세 조회에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        raise InternalServerError(
            message="그래프 히스토리 조회에 실패했습니다.",
            data=str(e),
        )


# 그래프 히스토리 생성
@router.post(
    "",
    response_model=ResponseModel,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_graph_history(
    request: Request,
    response: Response,
    graph_history: GraphHistoryCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    그래프 히스토리 생성 API
    """
    try:
        response_data = await graph_history_service.create_graph_history(
            db=db,
            graph_history=graph_history,
        )
        return ResponseModel(
            status=http_status.HTTP_201_CREATED,
            message="그래프 히스토리 생성에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="그래프 히스토리 생성에 실패했습니다.",
            data=str(e),
        )


# 엣지 수정
@router.put("/{graph_history_id}", response_model=ResponseModel)
async def update_graph_history(
    request: Request,
    response: Response,
    graph_history_id: UUID4,
    graph_history: GraphHistoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    그래프 히스토리 수정 API
    """
    try:
        response_data = await graph_history_service.update_graph_history(
            db=db,
            graph_history_id=graph_history_id,
            graph_history=graph_history,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 히스토리 수정에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="그래프 히스토리 수정에 실패했습니다.",
            data=str(e),
        )


# 그래프 히스토리 삭제
@router.delete(
    "/{graph_history_id}",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
)
async def delete_graph_history(
    request: Request,
    response: Response,
    graph_history_id: UUID4 = Path(..., description="그래프 히스토리 ID"),
    graph_history: GraphHistoryDeleteRequest = Body(
        ..., description="그래프 히스토리 삭제 요청"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    그래프 히스토리 삭제 API
    """
    try:
        response_data = await graph_history_service.delete_graph_history(
            db=db,
            graph_history_id=graph_history_id,
            graph_history=graph_history,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 히스토리 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="그래프 히스토리 삭제에 실패했습니다.",
            data=str(e),
        )


# 그래프 히스토리 삭제(hard delete)
@router.delete(
    "/{graph_history_id}/hard-delete",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_graph_histories_hard(
    request: Request,
    response: Response,
    graph_history_id: UUID4 = Path(..., description="그래프 히스토리 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    그래프 히스토리 삭제(hard delete) API
    """
    try:
        response_data = await graph_history_service.delete_graph_history_hard(
            db=db,
            graph_history_id=graph_history_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 히스토리 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="그래프 히스토리 삭제에 실패했습니다.",
            data=str(e),
        )
