from app.core.exception import (
    NotFoundError,
    InternalServerError,
    CustomException,
)
from app.database.crud.rag import chunk as chunk_crud
from app.schemas.rag.chunk import (
    ChunkDetail,
    ChunkResponse,
    ChunksResponse,
    ChunkCreateRequest,
    ChunkUpdateRequest,
    ChunkDeleteRequest,
    ChunkIdResponse,
    ChunkIdsResponse,
)
from app.schemas.pagination import Pagination
from app.utils.common import convert_sqlalchemy_to_pydantic
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4
from uuid import UUID

"""
여기에 Chunk 서비스 함수를 구현합니다.
서비스 레이어에는 아래와 같은 역할을 합니다.
    - 비즈니스 로직 구현
    - 데이터 유효성 검사
    - crud 상태를 보고 적절한 커스텀 에러 raise
    - 트랜잭션 관리(db commit, rollback)
    - sqlalchemy 객체를 pydantic model로 validation
    - API의 전체 로직 흐름 제어
"""


async def get_chunks(
    db: AsyncSession,
    page: int = 0,
    size: int = 10,
    chunk_id: Optional[UUID4] = None,
    document_id: Optional[UUID4] = None,
    chunk_index: Optional[int] = None,
    content: Optional[str] = None,
    embedding_id: Optional[str] = None,
    chunk_size: Optional[int] = None,
    overlap_size: Optional[int] = None,
    method: Optional[str] = None,
    sort: Optional[str] = "created_at:desc",
):
    """
    청크 목록과 페이징 데이터를 조합하는 서비스 함수
    """
    try:
        # size None일 시 전체 목록 조회
        skip, limit = (0, None) if size is None else (page * size, size)

        # 청크 목록과 전체 청크 수 조회
        total_count, db_chunks = await chunk_crud.read_chunks(
            db,
            skip=skip,
            limit=limit,
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

        # Pagination 객체 생성 (utils의 Pagination 사용하여 0으로 나누기 문제 해결)
        pagination = Pagination.create(
            total_count=total_count or 0,
            current_page=page,
            page_size=size if size is not None else (total_count or 0),
        )

        # 청크 데이터 변환
        chunks = [
            convert_sqlalchemy_to_pydantic(chunk, ChunkDetail)
            for chunk in db_chunks
        ]

        # 최종 응답 반환
        return pagination, ChunksResponse(chunks=chunks)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def get_chunk(
    db: AsyncSession,
    chunk_id: UUID4,
) -> ChunkResponse:
    """
    청크 데이터를 가져오는 서비스 함수
    """
    try:
        db_chunk = await chunk_crud.read_chunk(db, chunk_id=chunk_id)
        if db_chunk is None:
            raise NotFoundError()

        # SQLAlchemy 객체를 Pydantic 모델로 변환
        chunk_detail = convert_sqlalchemy_to_pydantic(db_chunk, ChunkDetail)

        return ChunkResponse(chunk=chunk_detail)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def create_chunk(
    db: AsyncSession,
    chunk: ChunkCreateRequest,
) -> ChunkIdResponse:
    """
    청크 데이터를 생성하는 서비스 함수
    """
    try:
        db_chunk = await chunk_crud.create_chunk(
            db,
            chunk=chunk,
        )
        await db.commit()
        await db.refresh(db_chunk)
        return ChunkIdResponse(id=UUID(str(db_chunk.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def update_chunk(
    db: AsyncSession,
    chunk_id: UUID4,
    chunk: ChunkUpdateRequest,
) -> ChunkIdResponse:
    """
    청크 데이터를 수정하는 서비스 함수
    """
    try:
        db_chunk = await chunk_crud.read_chunk(
            db,
            chunk_id=chunk_id,
            update_lock=True,
        )
        if db_chunk is None:
            raise NotFoundError()

        db_chunk = await chunk_crud.update_chunk(
            db_chunk=db_chunk,
            chunk=chunk,
        )
        await db.commit()
        await db.refresh(db_chunk)
        return ChunkIdResponse(id=UUID(str(db_chunk.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_chunk(
    db: AsyncSession,
    chunk_id: UUID4,
    chunk: ChunkDeleteRequest,
) -> ChunkIdResponse:
    """
    청크 데이터를 삭제하는 서비스 함수
    """
    try:
        db_chunk = await chunk_crud.read_chunk(
            db,
            chunk_id=chunk_id,
            update_lock=True,
        )
        db_chunk = await chunk_crud.delete_chunk(
            db_chunk=db_chunk,
            updated_by=chunk.updated_by,
        )
        if not db_chunk:
            raise NotFoundError()
        await db.commit()
        await db.refresh(db_chunk)
        return ChunkIdResponse(id=UUID(str(db_chunk.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_chunk_hard(
    db: AsyncSession,
    chunk_id: UUID4,
    chunk: ChunkDeleteRequest,
) -> ChunkIdResponse:
    """
    청크 데이터를 하드 삭제하는 서비스 함수
    """
    try:
        db_chunk = await chunk_crud.read_chunk(
            db,
            chunk_id=chunk_id,
            update_lock=True,
        )
        db_chunk = await chunk_crud.delete_chunk_hard(
            db_chunk=db_chunk,
            db=db,
        )
        if not db_chunk:
            raise NotFoundError()
        await db.commit()
        await db.refresh(db_chunk)
        return ChunkIdResponse(id=UUID(str(db_chunk.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))
