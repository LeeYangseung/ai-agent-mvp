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
from app.schemas.graph.node import (
    NodeCreateRequest,
    NodeUpdateRequest,
    NodeDeleteRequest,
)
from app.services.graph import node as node_service
from app.core.logging import get_logger

logger = get_logger("app")

router = APIRouter()


@router.get("", response_model=ResponseModel)
async def get_node_list(
    request: Request,
    response: Response,
    page: int = Query(0, ge=0, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    node_uuid: Optional[UUID4] = Query(None, description="노드 UUID(Filter)"),
    graph_id: Optional[UUID4] = Query(None, description="그래프 ID(Filter)"),
    node_id: Optional[str] = Query(None, description="노드 ID(Search)"),
    type: Optional[str] = Query(None, description="노드 타입(Filter)"),
    order: Optional[int] = Query(None, description="노드 순서(Filter)"),
    db: AsyncSession = Depends(get_db),
):
    """
    노드 목록 조회 API
    """
    try:
        pagination, response_data = await node_service.get_nodes(
            db=db,
            page=page,
            size=size,
            node_uuid=node_uuid,
            node_id=node_id,
            graph_id=graph_id,
            type=type,
            order=order,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="노드 목록 조회에 성공했습니다.",
            pagination=pagination,
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="노드 목록 조회에 실패했습니다.",
            data=str(e),
        )


# 노드 상세 조회
@router.get("/{node_uuid}", response_model=ResponseModel)
async def get_node(
    request: Request,
    response: Response,
    node_uuid: UUID4 = Path(..., description="노드 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    노드 상세 조회 API
    """
    try:
        response_data = await node_service.get_node(
            db=db,
            node_uuid=node_uuid,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="노드 상세 조회에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        raise InternalServerError(
            message="노드 조회에 실패했습니다.",
            data=str(e),
        )


# 노드 생성
@router.post(
    "",
    response_model=ResponseModel,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_node(
    request: Request,
    response: Response,
    node: NodeCreateRequest = Body(..., description="노드 생성 요청"),
    db: AsyncSession = Depends(get_db),
):
    """
    노드 생성 API
    """
    try:
        response_data = await node_service.create_node(
            db=db,
            node=node,
        )
        return ResponseModel(
            status=http_status.HTTP_201_CREATED,
            message="노드 생성에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="노드 생성에 실패했습니다.",
            data=str(e),
        )


# 노드 수정
@router.put("/{node_uuid}", response_model=ResponseModel)
async def update_node(
    request: Request,
    response: Response,
    node_uuid: UUID4,
    node: NodeUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    노드 수정 API
    """
    try:
        response_data = await node_service.update_node(
            db=db,
            node_uuid=node_uuid,
            node=node,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="노드 수정에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="노드 수정에 실패했습니다.",
            data=str(e),
        )


# 노드 삭제
@router.delete(
    "/{node_uuid}",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
)
async def delete_node(
    request: Request,
    response: Response,
    node_uuid: UUID4 = Path(..., description="노드 ID"),
    node: NodeDeleteRequest = Body(..., description="노드 삭제 요청"),
    db: AsyncSession = Depends(get_db),
):
    """
    노드 삭제 API
    """
    try:
        response_data = await node_service.delete_node(
            db=db,
            node_uuid=node_uuid,
            node=node,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="노드 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="노드 삭제에 실패했습니다.",
            data=str(e),
        )


# 노드 삭제(hard delete)
@router.delete(
    "/{node_uuid}/hard-delete",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_nodes_hard(
    request: Request,
    response: Response,
    node_uuid: UUID4 = Path(..., description="노드 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    노드 삭제(hard delete) API
    """
    try:
        response_data = await node_service.delete_node_hard(
            db=db,
            node_uuid=node_uuid,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="노드 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="노드 삭제에 실패했습니다.",
            data=str(e),
        )
