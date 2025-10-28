from fastapi import (
    APIRouter,
    Depends,
    Request,
    status as http_status,
    Response,
    Query,
    Path,
    Body,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4
from app.core.deps import get_db
from app.core.exception import InternalServerError, CustomException
from app.schemas.base import ResponseModel
from app.schemas.rag.document import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentDeleteRequest,
)
from app.services.rag import document as document_service
from app.core.logging import get_logger
from app.schemas.enums import DocumentStatus

logger = get_logger("app")

router = APIRouter()


# 문서 목록 조회
@router.get("", response_model=ResponseModel)
async def get_document_list(
    request: Request,
    response: Response,
    page: int = Query(0, ge=0, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    document_id: Optional[UUID4] = Query(None, description="문서 ID(Filter)"),
    chunk_id: Optional[UUID4] = Query(None, description="청크 ID(Filter)"),
    document_name: Optional[str] = Query(
        None, description="문서 이름(Search)"
    ),
    chunk_content: Optional[str] = Query(
        None, description="청크 내용(Search)"
    ),
    path: Optional[str] = Query(None, description="문서 경로(Filter)"),
    status: Optional[DocumentStatus] = Query(
        None, description="문서 상태(Filter)"
    ),
    sort: Optional[str] = Query(
        "created_at:desc",
        description="정렬 조건 (예: created_at:asc,document_name:desc)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    문서 목록 조회 API
    """
    try:
        pagination, response_data = await document_service.get_documents(
            db=db,
            page=page,
            size=size,
            document_id=document_id,
            chunk_id=chunk_id,
            document_name=document_name,
            chunk_content=chunk_content,
            path=path,
            status=status,
            sort=sort,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="문서 목록 조회에 성공했습니다.",
            pagination=pagination,
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="문서 목록 조회에 실패했습니다.",
            data=str(e),
        )


# 문서 상세 조회
@router.get("/{document_id}", response_model=ResponseModel)
async def get_document(
    request: Request,
    response: Response,
    document_id: UUID4 = Path(..., description="문서 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    문서 상세 조회 API
    """
    try:
        response_data = await document_service.get_document(
            db=db,
            document_id=document_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="문서 상세 조회에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        raise InternalServerError(
            message="문서 조회에 실패했습니다.",
            data=str(e),
        )


# 문서 생성
@router.post(
    "",
    response_model=ResponseModel,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_document(
    request: Request,
    response: Response,
    file: UploadFile = File(..., description="문서 파일"),
    name: str = Form(..., description="문서 이름"),
    chunk_size: Optional[int] = Form(
        default=500, description="청킹 전략 - 청크 크기"
    ),
    overlap_size: Optional[int] = Form(
        default=100, description="청킹 전략 - 오버랩 크기"
    ),
    method: Optional[str] = Form(
        default="overlap", description="청킹 전략 - 청크 방법"
    ),
    status: Optional[DocumentStatus] = Form(
        default=DocumentStatus.pending, description="문서 상태"
    ),
    created_by: Optional[str] = Form(default="admin", description="생성자"),
    updated_by: Optional[str] = Form(default="admin", description="수정자"),
    db: AsyncSession = Depends(get_db),
):
    """
    문서 생성 API
    """
    try:
        # Form 데이터로부터 DocumentCreateRequest 생성
        document = DocumentCreateRequest(
            name=name,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            method=method,
            status=status,
            created_by=created_by,
            updated_by=updated_by,
        )

        response_data = await document_service.create_document(
            db=db,
            document=document,
            file=file,
        )
        return ResponseModel(
            status=http_status.HTTP_201_CREATED,
            message="문서 생성에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="문서 생성에 실패했습니다.",
            data=str(e),
        )


# 문서 수정
@router.put("/{document_id}", response_model=ResponseModel)
async def update_document(
    request: Request,
    response: Response,
    document_id: UUID4,
    document: DocumentUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    문서 수정 API
    """
    try:
        response_data = await document_service.update_document(
            db=db,
            document_id=document_id,
            document=document,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="문서 수정에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="문서 수정에 실패했습니다.",
            data=str(e),
        )


# 문서 삭제
@router.delete(
    "/{document_id}",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
)
async def delete_document(
    request: Request,
    response: Response,
    document_id: UUID4 = Path(..., description="문서 ID"),
    document: DocumentDeleteRequest = Body(..., description="문서 삭제 요청"),
    db: AsyncSession = Depends(get_db),
):
    """
    문서 삭제 API
    """
    try:
        response_data = await document_service.delete_document(
            db=db,
            document_id=document_id,
            document=document,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="문서 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="문서 삭제에 실패했습니다.",
            data=str(e),
        )


# 문서 삭제(hard delete)
@router.delete(
    "/{document_id}/hard-delete",
    response_model=ResponseModel,
    status_code=http_status.HTTP_200_OK,
    include_in_schema=False,
)
async def delete_document_hard(
    request: Request,
    response: Response,
    document_id: UUID4 = Path(..., description="문서 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    문서 삭제(hard delete) API
    """
    try:
        response_data = await document_service.delete_document_hard(
            db=db,
            document_id=document_id,
        )
        return ResponseModel(
            status=http_status.HTTP_200_OK,
            message="문서 삭제에 성공했습니다.",
            data=response_data,
        )
    except CustomException as ce:
        logger.exception(f"{str(ce)}")
        raise
    except Exception as e:
        logger.exception(f"{str(e)}")
        raise InternalServerError(
            message="문서 삭제에 실패했습니다.",
            data=str(e),
        )
