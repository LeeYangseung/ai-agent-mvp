import datetime
from typing import Optional
from pydantic import UUID4
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.rag.collection import Collection as CollectionModel
from app.database.models.rag.document import Document as DocumentModel
from app.schemas.rag.collection import (
    CollectionCreateRequest,
    CollectionUpdateRequest,
)
from app.database.models.base import generate_uuid
from app.utils.common import parse_sort_conditions


"""
여기에 Collection CRUD 함수를 구현합니다.
CRUD 함수에는 아래와 같은 역할을 합니다.
    - 데이터베이스 조회, 생성, 수정, 삭제 작업 수행
    - 데이터 존재 시 sqlalchemy 객체 반환, 데이터가 존재하지 않을 때는 None을 반환
CRUD 함수에서는 다음과 같은 처리를 하지 않아야 합니다.
    - db commit, rollback
    - 존재 여부, 데이터 유효성 판단 등 비즈니스 관점의 예외 처리
"""


async def create_collection(
    db: AsyncSession,
    collection: CollectionCreateRequest,
    created_by: Optional[str] = None,
):
    """컬렉션 생성"""
    db_collection = CollectionModel(
        id=str(generate_uuid()),
        name=collection.name,
        description=collection.description,
        is_deleted=False,
        created_at=datetime.datetime.now(),
        created_by=created_by if created_by else collection.created_by,
        updated_at=datetime.datetime.now(),
        updated_by=created_by if created_by else collection.created_by,
    )
    db.add(db_collection)
    return db_collection


async def read_collections(
    db: AsyncSession,
    skip: int = 0,
    limit: Optional[int] = None,
    collection_id: Optional[UUID4] = None,
    collection_name: Optional[str] = None,
    sort: Optional[str] = None,
):
    """컬렉션 목록 조회"""
    # Document 개수를 카운트하기 위한 서브쿼리
    document_count_subquery = (
        select(
            DocumentModel.collection_id,
            func.count(DocumentModel.id).label("document_count"),
        )
        .where(DocumentModel.is_deleted.is_(False))
        .group_by(DocumentModel.collection_id)
        .subquery()
    )

    # 메인 쿼리
    query = (
        select(
            CollectionModel,
            func.coalesce(document_count_subquery.c.document_count, 0).label(
                "document_count"
            ),
        )
        .outerjoin(
            document_count_subquery,
            CollectionModel.id == document_count_subquery.c.collection_id,
        )
        .where(CollectionModel.is_deleted.is_(False))
    )

    # Filter 적용
    filter_conditions = []
    if collection_id:
        filter_conditions.append(CollectionModel.id == str(collection_id))
    if filter_conditions:
        query = query.where(and_(*filter_conditions))

    # Search 적용
    search_conditions = []
    if collection_name:
        search_conditions.append(
            CollectionModel.name.ilike(f"%{collection_name}%")
        )
    if search_conditions:
        query = query.where(or_(*search_conditions))

    # Total count 쿼리 (페이징 전)
    total_count_query = select(func.count()).select_from(query.subquery())

    # Order 적용
    if sort:
        order_conditions = parse_sort_conditions(sort, CollectionModel)
        query = query.order_by(*order_conditions)
    else:
        query = query.order_by(CollectionModel.created_at.desc())

    # Pagination 적용
    if limit:
        query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    total_count = await db.scalar(total_count_query)

    # 결과를 (collection, document_count) 튜플로 반환
    collections_with_count = result.all()

    return total_count, collections_with_count


async def read_collection(
    db: AsyncSession,
    collection_id: UUID4,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    """컬렉션 단건 조회"""
    # Document 개수 카운트
    document_count_subquery = (
        select(func.count(DocumentModel.id).label("document_count"))
        .where(DocumentModel.collection_id == str(collection_id))
        .where(DocumentModel.is_deleted.is_(False))
        .scalar_subquery()
    )

    query = select(
        CollectionModel,
        func.coalesce(document_count_subquery, 0).label("document_count"),
    ).where(CollectionModel.id == str(collection_id))

    if is_deleted is not None:
        query = query.where(CollectionModel.is_deleted.is_(is_deleted))

    if update_lock:
        query = query.with_for_update()

    result = await db.execute(query)
    return result.first()


async def read_collection_by_name(
    db: AsyncSession,
    name: str,
    is_deleted: Optional[bool] = None,
):
    """컬렉션 이름으로 조회 (중복 체크용)"""
    query = select(CollectionModel).where(CollectionModel.name == name)

    if is_deleted is not None:
        query = query.where(CollectionModel.is_deleted.is_(is_deleted))

    result = await db.execute(query)
    return result.scalars().first()


async def update_collection(
    db_collection: CollectionModel,
    collection: CollectionUpdateRequest,
    updated_by: Optional[str] = None,
):
    """컬렉션 수정"""
    for key, value in collection.model_dump(exclude_unset=True).items():
        if hasattr(db_collection, key) and value is not None:
            setattr(db_collection, key, value)

    db_collection.updated_at = datetime.datetime.now()
    db_collection.updated_by = (
        updated_by if updated_by else db_collection.updated_by
    )
    return db_collection


async def delete_collection(
    db_collection: CollectionModel,
    updated_by: Optional[str] = None,
):
    """컬렉션 Soft Delete"""
    if not db_collection:
        return None

    db_collection.is_deleted = True
    db_collection.updated_at = datetime.datetime.now()
    db_collection.updated_by = (
        updated_by if updated_by else db_collection.updated_by
    )

    return db_collection


async def delete_collection_hard(
    db_collection: CollectionModel,
    db: AsyncSession,
):
    """컬렉션 Hard Delete"""
    if not db_collection:
        return None

    await db.delete(db_collection)
    return db_collection


async def count_documents_in_collection(
    db: AsyncSession,
    collection_id: UUID4,
):
    """컬렉션에 속한 문서 개수 조회"""
    query = (
        select(func.count(DocumentModel.id))
        .where(DocumentModel.collection_id == str(collection_id))
        .where(DocumentModel.is_deleted.is_(False))
    )
    result = await db.scalar(query)
    return result or 0
