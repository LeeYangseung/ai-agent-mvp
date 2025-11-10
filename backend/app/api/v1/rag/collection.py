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
from app.schemas.rag.collection import (
    CollectionCreateRequest,
    CollectionUpdateRequest,
    CollectionDeleteRequest,
)
from app.services.rag import collection as collection_service
from app.core.logging import get_logger

logger = get_logger("app")

router = APIRouter()


# 컬렉션 목록 조회
@router.get("", response_model=ResponseModel)
async def get_collection_list(
    request: Request,
    response: Response,
    page: int = Query(0, ge=0, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    collection_id: Optional[UUID4] = Query(
        None, description="컬렉션 ID(Filter)"
    ),
    collection_name: Optional[str] = Query(
        None, description="컬렉션 이름(Search)"
    ),
    sort: Optional[str] = Query(
        "created_at:desc",
        description="정렬 조건 (예: created_at:asc,name:desc)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    컬렉션 목록 조회 API
    """
    try:
        pagination, response_data = await collection_service.get_collections(
            db=db,
            page=page,
            size=size,
            collection_id=collection_id,
            collection_name=collection_name,
            sort=sort,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="컬렉션 목록 조회에 성공했습니다.",
            pagination=pagination,
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="컬렉션 목록 조회에 실패했습니다.",
            data=str(e),
        )


# 컬렉션 상세 조회
@router.get("/{collection_id}", response_model=ResponseModel)
async def get_collection(
    request: Request,
    response: Response,
    collection_id: UUID4 = Path(..., description="컬렉션 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    컬렉션 상세 조회 API
    """
    try:
        response_data = await collection_service.get_collection(
            db=db,
            collection_id=collection_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="컬렉션 상세 조회에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="컬렉션 조회에 실패했습니다.",
            data=str(e),
        )


# 컬렉션 생성
@router.post(
    "",
    response_model=ResponseModel,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_collection(
    request: Request,
    response: Response,
    collection: CollectionCreateRequest = Body(
        ..., description="컬렉션 생성 요청"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    컬렉션 생성 API
    """
    try:
        response_data = await collection_service.create_collection(
            db=db,
            collection=collection,
        )
        return ResponseModel(
            status=http_status.HTTP_201_CREATED,
            message="컬렉션 생성에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="컬렉션 생성에 실패했습니다.",
            data=str(e),
        )


# 컬렉션 수정
@router.put("/{collection_id}", response_model=ResponseModel)
async def update_collection(
    request: Request,
    response: Response,
    collection_id: UUID4 = Path(..., description="컬렉션 ID"),
    collection: CollectionUpdateRequest = Body(
        ..., description="컬렉션 수정 요청"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    컬렉션 수정 API
    """
    try:
        response_data = await collection_service.update_collection(
            db=db,
            collection_id=collection_id,
            collection=collection,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="컬렉션 수정에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="컬렉션 수정에 실패했습니다.",
            data=str(e),
        )


# 컬렉션 삭제
@router.delete(
    "/{collection_id}",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
)
async def delete_collection(
    request: Request,
    response: Response,
    collection_id: UUID4 = Path(..., description="컬렉션 ID"),
    collection: CollectionDeleteRequest = Body(
        ..., description="컬렉션 삭제 요청"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    컬렉션 삭제 API (Soft Delete)
    컬렉션에 문서가 있으면 삭제 불가
    """
    try:
        response_data = await collection_service.delete_collection(
            db=db,
            collection_id=collection_id,
            collection=collection,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="컬렉션 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="컬렉션 삭제에 실패했습니다.",
            data=str(e),
        )


# 컬렉션 삭제(hard delete)
@router.delete(
    "/{collection_id}/hard-delete",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_collection_hard(
    request: Request,
    response: Response,
    collection_id: UUID4 = Path(..., description="컬렉션 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    컬렉션 삭제(hard delete) API
    컬렉션에 문서가 있으면 삭제 불가
    """
    try:
        response_data = await collection_service.delete_collection_hard(
            db=db,
            collection_id=collection_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="컬렉션 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="컬렉션 삭제에 실패했습니다.",
            data=str(e),
        )
