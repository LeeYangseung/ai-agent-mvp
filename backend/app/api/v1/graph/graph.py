from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    Path,
    Query,
    Body,
    status as http_status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4

from app.schemas.graph.graph import (
    GraphCreateRequest,
    GraphUpdateRequest,
    GraphRunRequest,
    GraphDeleteRequest,
)
from app.core.graph_runner import run_graph
from app.core.logging import get_logger
from app.core.deps import get_llm, get_db
from app.core.exception import CustomException, InternalServerError
from app.schemas.base import ResponseModel
from app.services.graph import graph as graph_service

logger = get_logger("app")
router = APIRouter()


@router.post("/run-graph")
async def run_graph_api(req: GraphRunRequest, llm=Depends(get_llm)):
    logger.info(f"Running graph: {req.dict()}")
    result = await run_graph(req.dict(), llm)

    # 구조화된 응답 반환
    return {
        "results": result["structured_results"],  # 새로운 구조화된 데이터
        "final_state": result["final_state"],  # 기존 호환성을 위한 원본 데이터
    }


@router.get("", response_model=ResponseModel)
async def get_graph_list(
    request: Request,
    response: Response,
    page: int = Query(0, ge=0),
    size: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None, description="그래프 이름(Search)"),
    description: Optional[str] = Query(
        None, description="그래프 설명(Search)"
    ),
    version: Optional[int] = Query(None, description="그래프 버전(Filter)"),
    sort: Optional[str] = Query(
        "created_at:desc",
        description="정렬 조건 (예: created_at:asc,name:desc)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """그래프 목록 조회 API"""
    try:
        pagination, response_data = await graph_service.get_graphs(
            db=db,
            page=page,
            size=size,
            name=name,
            description=description,
            version=version,
            sort=sort,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 목록 조회에 성공했습니다.",
            pagination=pagination,
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(
            message="그래프 목록 조회에 실패했습니다.",
            data=str(e),
        )


@router.get("/{graph_id}", response_model=ResponseModel)
async def get_graph(
    request: Request,
    response: Response,
    graph_id: UUID4 = Path(..., description="그래프 ID"),
    db: AsyncSession = Depends(get_db),
):
    """그래프 상세 조회 API"""
    try:
        response_data = await graph_service.get_graph(
            db=db,
            graph_id=graph_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 상세 조회에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(
            message="그래프 상세 조회에 실패했습니다.",
            data=str(e),
        )


@router.post(
    "",
    response_model=ResponseModel,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_graph(
    request: Request,
    response: Response,
    graph: GraphCreateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """그래프 생성"""
    try:
        response_data = await graph_service.create_graph(
            db=db,
            graph=graph,
        )
        return ResponseModel(
            status=http_status.HTTP_201_CREATED,
            message="그래프 생성에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(
            message="그래프 생성에 실패했습니다.",
            data=str(e),
        )


@router.put("/{graph_id}", response_model=ResponseModel)
async def update_graph(
    request: Request,
    response: Response,
    graph_id: UUID4 = Path(...),
    graph: GraphUpdateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """그래프 수정"""
    try:
        response_data = await graph_service.update_graph(
            db=db,
            graph_id=graph_id,
            graph=graph,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 수정에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(
            message="그래프 수정에 실패했습니다.",
            data=str(e),
        )


@router.delete("/{graph_id}", response_model=ResponseModel)
async def delete_graph(
    request: Request,
    response: Response,
    graph_id: UUID4 = Path(...),
    graph: GraphDeleteRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """그래프 삭제"""
    try:
        response_data = await graph_service.delete_graph(
            db=db,
            graph_id=graph_id,
            graph=graph,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(
            message="그래프 삭제에 실패했습니다.",
            data=str(e),
        )


@router.delete(
    "/{graph_id}/hard-delete",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_graph_hard(
    request: Request,
    response: Response,
    graph_id: UUID4 = Path(..., description="그래프 ID"),
    db: AsyncSession = Depends(get_db),
):
    """그래프 삭제(hard delete) API"""
    try:
        response_data = await graph_service.delete_graph_hard(
            db=db,
            graph_id=graph_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="그래프 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(str(e))
        raise InternalServerError(
            message="그래프 삭제에 실패했습니다.",
            data=str(e),
        )
