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
from app.schemas.graph.edge import (
    EdgeCreateRequest,
    EdgeUpdateRequest,
    EdgeDeleteRequest,
)
from app.services.graph import edge as edge_service
from app.core.logging import get_logger

logger = get_logger("app")

router = APIRouter()


# 엣지 목록 조회
@router.get("", response_model=ResponseModel)
async def get_edge_list(
    request: Request,
    response: Response,
    page: int = Query(0, ge=0, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    edge_id: Optional[UUID4] = Query(None, description="엣지 ID(Filter)"),
    graph_id: Optional[UUID4] = Query(None, description="그래프 ID(Filter)"),
    source: Optional[str] = Query(None, description="소스 노드 ID(Filter)"),
    target: Optional[str] = Query(None, description="타겟 노드 ID(Filter)"),
    db: AsyncSession = Depends(get_db),
):
    """
    엣지 목록 조회 API
    """
    try:
        pagination, response_data = await edge_service.get_edges(
            db=db,
            page=page,
            size=size,
            edge_id=edge_id,
            graph_id=graph_id,
            source=source,
            target=target,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="엣지 목록 조회에 성공했습니다.",
            pagination=pagination,
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="엣지 목록 조회에 실패했습니다.",
            data=str(e),
        )


# 엣지 상세 조회
@router.get("/{edge_id}", response_model=ResponseModel)
async def get_edge(
    request: Request,
    response: Response,
    edge_id: UUID4 = Path(..., description="엣지 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    엣지 상세 조회 API
    """
    try:
        response_data = await edge_service.get_edge(
            db=db,
            edge_id=edge_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="엣지 상세 조회에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        raise InternalServerError(
            message="엣지 조회에 실패했습니다.",
            data=str(e),
        )


# 엣지 생성
@router.post(
    "",
    response_model=ResponseModel,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_edge(
    request: Request,
    response: Response,
    edge: EdgeCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    엣지 생성 API
    """
    try:
        response_data = await edge_service.create_edge(
            db=db,
            edge=edge,
        )
        return ResponseModel(
            status=http_status.HTTP_201_CREATED,
            message="엣지 생성에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="엣지 생성에 실패했습니다.",
            data=str(e),
        )


# 엣지 수정
@router.put("/{edge_id}", response_model=ResponseModel)
async def update_edge(
    request: Request,
    response: Response,
    edge_id: UUID4,
    edge: EdgeUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    엣지 수정 API
    """
    try:
        response_data = await edge_service.update_edge(
            db=db,
            edge_id=edge_id,
            edge=edge,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="엣지 수정에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="엣지 수정에 실패했습니다.",
            data=str(e),
        )


# 엣지 삭제
@router.delete(
    "/{edge_id}",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
)
async def delete_node(
    request: Request,
    response: Response,
    edge_id: UUID4 = Path(..., description="엣지 ID"),
    edge: EdgeDeleteRequest = Body(..., description="엣지 삭제 요청"),
    db: AsyncSession = Depends(get_db),
):
    """
    엣지 삭제 API
    """
    try:
        response_data = await edge_service.delete_edge(
            db=db,
            edge_id=edge_id,
            edge=edge,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="엣지 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="엣지 삭제에 실패했습니다.",
            data=str(e),
        )


# 엣지 삭제(hard delete)
@router.delete(
    "/{edge_id}/hard-delete",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_edges_hard(
    request: Request,
    response: Response,
    edge_id: UUID4 = Path(..., description="엣지 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    엣지 삭제(hard delete) API
    """
    try:
        response_data = await edge_service.delete_edge_hard(
            db=db,
            edge_id=edge_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="엣지 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="엣지 삭제에 실패했습니다.",
            data=str(e),
        )
