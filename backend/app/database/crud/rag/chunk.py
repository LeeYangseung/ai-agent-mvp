from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from pydantic import UUID4
from typing import List, Optional, Sequence
import datetime

from app.database.models.rag.chunk import Chunk as ChunkModel
from app.schemas.rag.chunk import ChunkCreateRequest, ChunkUpdateRequest
from app.database.models.base import generate_uuid
from app.utils.common import parse_sort_conditions

"""
여기에 Chunk CRUD 함수를 구현합니다.
CRUD 함수에는 아래와 같은 역할을 합니다.
    - 데이터베이스 조회, 생성, 수정, 삭제 작업 수행
    - 데이터 존재 시 sqlalchemy 객체 반환, 데이터가 존재하지 않을 때는 None을 반환
CRUD 함수에서는 다음과 같은 처리를 하지 않아야 합니다.
    - db commit, rollback
    - 존재 여부, 데이터 유효성 판단 등 비즈니스 관점의 예외 처리
"""


async def create_chunk(
    db: AsyncSession,
    chunk: ChunkCreateRequest,
    created_by: Optional[UUID4] = None,
):
    """Chunk 생성(INSERT)"""
    db_chunk = ChunkModel(
        id=str(generate_uuid()),
        document_id=str(chunk.document_id),
        chunk_index=chunk.chunk_index,
        content=chunk.content,
        embedding_id=chunk.embedding_id,
        chunk_size=chunk.chunk_size,
        is_deleted=False,
        created_at=datetime.datetime.now(),
        created_by=created_by if created_by else chunk.created_by,
        updated_at=datetime.datetime.now(),
        updated_by=created_by if created_by else chunk.created_by,
    )
    db.add(db_chunk)
    return db_chunk


async def read_chunks(
    db: AsyncSession,
    skip: int = 0,
    limit: Optional[int] = 10,
    chunk_id: Optional[UUID4] = None,
    document_id: Optional[UUID4] = None,
    chunk_index: Optional[int] = None,
    content: Optional[str] = None,
    embedding_id: Optional[str] = None,
    chunk_size: Optional[int] = None,
    sort: Optional[str] = None,
):
    query = select(ChunkModel).where(ChunkModel.is_deleted.is_(False))

    # Filter 적용
    filter_conditions = []
    if chunk_id:
        filter_conditions.append(ChunkModel.id == str(chunk_id))
    if document_id:
        filter_conditions.append(ChunkModel.document_id == str(document_id))
    if chunk_index:
        filter_conditions.append(ChunkModel.chunk_index == chunk_index)
    if embedding_id:
        filter_conditions.append(ChunkModel.embedding_id == embedding_id)
    if chunk_size:
        filter_conditions.append(ChunkModel.chunk_size == chunk_size)
    if filter_conditions:
        query = query.where(and_(*filter_conditions))

    # Search 적용
    search_conditions = []
    if content:
        search_conditions.append(ChunkModel.content.ilike(f"%{content}%"))
    if search_conditions:
        query = query.where(or_(*search_conditions))

    # total_count를 위한 쿼리
    total_count_query = select(func.count()).select_from(ChunkModel)
    if query.whereclause is not None:
        total_count_query = total_count_query.where(query.whereclause)

    # Order 적용
    order_conditions = []
    if sort:
        order_conditions = parse_sort_conditions(sort, ChunkModel)
        query = query.order_by(*order_conditions)

    # Pagination 적용
    if limit:
        query = query.offset(skip).limit(limit)

    db_chunks = await db.execute(query)
    total_count = await db.scalar(total_count_query)
    return total_count, db_chunks.scalars().all()


async def read_chunks_by_chunk_ids(
    db: AsyncSession,
    chunk_ids: List[UUID4],
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    chunk_ids_str = [str(chunk_id) for chunk_id in chunk_ids]
    query = select(ChunkModel).where(ChunkModel.id.in_(chunk_ids_str))
    if is_deleted is not None:
        query = query.where(ChunkModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_chunks = await db.execute(query)
    return db_chunks.unique().scalars().all()


async def read_chunk(
    db: AsyncSession,
    chunk_id: UUID4,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    query = select(ChunkModel).where(ChunkModel.id == str(chunk_id))
    if is_deleted is not None:
        query = query.where(ChunkModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_chunk = await db.execute(query)
    return db_chunk.unique().scalars().first()


async def update_chunk(
    db_chunk: ChunkModel,
    chunk: ChunkUpdateRequest,
    updated_by: Optional[UUID4] = None,
):
    for key, value in chunk.model_dump(exclude_unset=True).items():
        if hasattr(db_chunk, key):  # ChunkModel에 해당 필드가 있는지 확인
            setattr(db_chunk, key, value)
    db_chunk.updated_at = datetime.datetime.now()
    db_chunk.updated_by = updated_by if updated_by else db_chunk.updated_by
    return db_chunk


async def delete_chunk(
    db_chunk: ChunkModel,
    updated_by: Optional[UUID4] = None,
):
    if not db_chunk:
        return None

    db_chunk.is_deleted = True
    db_chunk.updated_at = datetime.datetime.now()
    db_chunk.updated_by = updated_by if updated_by else db_chunk.updated_by

    return db_chunk


async def delete_chunk_hard(
    db_chunk: ChunkModel,
    db: AsyncSession,
):
    if not db_chunk:
        return None

    await db.delete(db_chunk)

    return db_chunk
