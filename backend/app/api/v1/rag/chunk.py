from fastapi import (
    APIRouter,
    Depends,
    Request,
    status as http_status,
    Response,
    Query,
    Path,
    Body,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4
from app.core.deps import get_db
from app.core.exception import InternalServerError, CustomException
from app.schemas.base import ResponseModel
from app.schemas.rag.chunk import (
    ChunkCreateRequest,
    ChunkUpdateRequest,
    ChunkDeleteRequest,
    ChunkIdResponse,
    ChunkIdsResponse,
)
from app.services.rag import chunk as chunk_service
from app.core.logging import get_logger

logger = get_logger("app")

router = APIRouter()


# 청크 목록 조회
@router.get("", response_model=ResponseModel)
async def get_chunk_list(
    request: Request,
    response: Response,
    page: int = Query(0, ge=0, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    chunk_id: Optional[UUID4] = Query(None, description="청크 ID(Filter)"),
    document_id: Optional[UUID4] = Query(None, description="문서 ID(Filter)"),
    chunk_index: Optional[int] = Query(
        None, description="청크 인덱스(Filter)"
    ),
    content: Optional[str] = Query(None, description="청크 내용(Search)"),
    embedding_id: Optional[str] = Query(
        None, description="VectorDB key(Filter)"
    ),
    chunk_size: Optional[int] = Query(None, description="청크 크기(Filter)"),
    overlap_size: Optional[int] = Query(
        None, description="청크 중복 크기(Filter)"
    ),
    method: Optional[str] = Query(None, description="청크 방법(Filter)"),
    sort: Optional[str] = Query(
        "created_at:desc",
        description="정렬 조건 (예: created_at:asc,chunk_index:desc)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    청크 목록 조회 API
    """
    try:
        pagination, response_data = await chunk_service.get_chunks(
            db=db,
            page=page,
            size=size,
            chunk_id=chunk_id,
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding_id=embedding_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            method=method,
            sort=sort,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="청크 목록 조회에 성공했습니다.",
            pagination=pagination,
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="청크 목록 조회에 실패했습니다.",
            data=str(e),
        )


# 청크 상세 조회
@router.get("/{chunk_id}", response_model=ResponseModel)
async def get_chunk(
    request: Request,
    response: Response,
    chunk_id: UUID4 = Path(..., description="청크 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    청크 상세 조회 API
    """
    try:
        response_data = await chunk_service.get_chunk(
            db=db,
            chunk_id=chunk_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="청크 상세 조회에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        raise InternalServerError(
            message="청크 조회에 실패했습니다.",
            data=str(e),
        )


# 청크 생성
@router.post(
    "",
    response_model=ResponseModel,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_chunk(
    request: Request,
    response: Response,
    chunk: ChunkCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    청크 생성 API
    """
    try:
        response_data = await chunk_service.create_chunk(
            db=db,
            chunk=chunk,
        )
        return ResponseModel(
            status=http_status.HTTP_201_CREATED,
            message="청크 생성에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="청크 생성에 실패했습니다.",
            data=str(e),
        )


# 청크 수정
@router.put("/{chunk_id}", response_model=ResponseModel)
async def update_chunk(
    request: Request,
    response: Response,
    chunk_id: UUID4,
    chunk: ChunkUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    청크 수정 API
    """
    try:
        response_data = await chunk_service.update_chunk(
            db=db,
            chunk_id=chunk_id,
            chunk=chunk,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="청크 수정에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="청크 수정에 실패했습니다.",
            data=str(e),
        )


# 청크 삭제
@router.delete(
    "/{chunk_id}",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
)
async def delete_chunk(
    request: Request,
    response: Response,
    chunk_id: UUID4 = Path(..., description="청크 ID"),
    chunk: ChunkDeleteRequest = Body(..., description="청크 삭제 요청"),
    db: AsyncSession = Depends(get_db),
):
    """
    청크 삭제 API
    """
    try:
        response_data = await chunk_service.delete_chunk(
            db=db,
            chunk_id=chunk_id,
            chunk=chunk,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="청크 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="청크 삭제에 실패했습니다.",
            data=str(e),
        )


# 청크 삭제(hard delete)
@router.delete(
    "/{chunk_id}/hard-delete",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_chunks_hard(
    request: Request,
    response: Response,
    chunk_id: UUID4 = Path(..., description="청크 ID"),
    chunk: ChunkDeleteRequest = Body(..., description="청크 삭제 요청"),
    db: AsyncSession = Depends(get_db),
):
    """
    청크 삭제(hard delete) API
    """
    try:
        response_data = await chunk_service.delete_chunk_hard(
            db=db,
            chunk_id=chunk_id,
            chunk=chunk,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="청크 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="청크 삭제에 실패했습니다.",
            data=str(e),
        )
