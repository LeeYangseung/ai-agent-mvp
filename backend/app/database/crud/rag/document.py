import datetime
from typing import List, Optional, Sequence
from pydantic import UUID4
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager
from app.schemas.enums import DocumentStatus

from app.database.models.rag.document import Document as DocumentModel
from app.database.models.rag.chunk import (
    Chunk as ChunkModel,
)
from app.schemas.rag.document import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
)
from app.database.models.base import generate_uuid
from app.utils.common import parse_sort_conditions


"""
여기에 Document CRUD 함수를 구현합니다.
CRUD 함수에는 아래와 같은 역할을 합니다.
    - 데이터베이스 조회, 생성, 수정, 삭제 작업 수행
    - 데이터 존재 시 sqlalchemy 객체 반환, 데이터가 존재하지 않을 때는 None을 반환
CRUD 함수에서는 다음과 같은 처리를 하지 않아야 합니다.
    - db commit, rollback
    - 존재 여부, 데이터 유효성 판단 등 비즈니스 관점의 예외 처리
"""


async def create_document(
    db: AsyncSession,
    document: DocumentCreateRequest,
    created_by: Optional[UUID4] = None,
):
    db_document = DocumentModel(
        id=str(generate_uuid()),
        name=document.name,
        path=document.path,
        chunk_size=document.chunk_size,
        overlap_size=document.overlap_size,
        method=document.method,
        status=document.status,
        is_deleted=False,
        created_at=datetime.datetime.now(),
        created_by=created_by if created_by else document.created_by,
        updated_at=datetime.datetime.now(),
        updated_by=created_by if created_by else document.created_by,
    )
    db.add(db_document)
    return db_document


async def read_documents(
    db: AsyncSession,
    skip: int = 0,
    limit: Optional[int] = None,
    document_id: Optional[UUID4] = None,
    chunk_id: Optional[UUID4] = None,
    document_name: Optional[str] = None,
    chunk_content: Optional[str] = None,
    path: Optional[str] = None,
    status: Optional[DocumentStatus] = None,
    sort: Optional[str] = None,
):
    # 쿼리에 Join이 들어가는 경우 search, filter, order, offset, limit의 정합성을 보장하기 위해
    # base_query로 조건에 해당하는 id값을 찾고, 해당 id를 기반으로 Main 쿼리 실행
    # 공통 조인 조건을 적용하는 헬퍼 함수
    def apply_common_joins(query):
        return query.outerjoin(
            ChunkModel,
            and_(
                DocumentModel.id == ChunkModel.document_id,
                or_(
                    ChunkModel.is_deleted.is_(False),  # ON 조건에서 필터링
                    ChunkModel.id.is_(None),
                ),
            ),
        ).where(DocumentModel.is_deleted.is_(False))

    # 1. 먼저 Document.id를 기준으로 서브쿼리를 생성하여 필터, 검색, 정렬 및 페이징을 적용
    base_query = select(
        DocumentModel.id,
    ).select_from(DocumentModel)

    base_query = apply_common_joins(base_query)

    # Filter 적용
    filter_conditions = []

    if document_id:
        filter_conditions.append(DocumentModel.id == str(document_id))
    if chunk_id:
        filter_conditions.append(ChunkModel.id == str(chunk_id))
    if status:
        filter_conditions.append(DocumentModel.status == status)
    if filter_conditions:
        base_query = base_query.where(and_(*filter_conditions))

    # Search 적용
    search_conditions = []

    if document_name:
        search_conditions.append(
            DocumentModel.name.ilike(f"%{document_name}%")
        )
    if chunk_content:
        search_conditions.append(
            ChunkModel.content.ilike(f"%{chunk_content}%")
        )
    if path:
        search_conditions.append(DocumentModel.path.ilike(f"%{path}%"))

    if search_conditions:
        base_query = base_query.where(or_(*search_conditions))

    # order 적용
    order_conditions = []
    if sort:
        order_conditions = parse_sort_conditions(sort, DocumentModel)
        # DISTINCT ON을 사용할 때는 첫 번째 ORDER BY 컬럼이 DISTINCT ON 컬럼과 일치해야 함
        # document.id를 먼저 추가하고, 그 다음에 원래 정렬 조건을 추가
        base_query = base_query.order_by(DocumentModel.id, *order_conditions)
    else:
        # sort가 없을 때는 기본적으로 document.id로 정렬
        base_query = base_query.order_by(DocumentModel.id)

    # Document.id로 distinct 적용
    base_query = base_query.distinct(DocumentModel.id)

    # total_count_query는 이 서브쿼리를 기반으로 전체 개수를 계산
    total_count_query = select(func.count()).select_from(base_query.subquery())

    # Pagination 적용
    if limit:
        base_query = base_query.offset(skip).limit(limit)

    document_ids_result = await db.execute(base_query)
    document_ids = [row[0] for row in document_ids_result.all()]

    # 2. 메인 쿼리: Document 데이터를 조회하고 관계 데이터를 eager 로딩
    main_query = select(DocumentModel).select_from(DocumentModel)
    main_query = apply_common_joins(main_query)
    main_query = main_query.where(DocumentModel.id.in_(document_ids))

    # 정렬 조건은 서브쿼리와 동일하게 적용
    if sort:
        order_conditions = parse_sort_conditions(sort, DocumentModel)
        main_query = main_query.order_by(*order_conditions)
    else:
        # 기본 정렬: created_at desc
        main_query = main_query.order_by(DocumentModel.created_at.desc())
    main_query = main_query.options(contains_eager(DocumentModel.chunks))

    db_document = await db.execute(main_query)
    total_count = await db.scalar(total_count_query)
    return total_count, db_document.unique().scalars().all()


async def read_documents_by_document_ids(
    db: AsyncSession,
    document_ids: List[UUID4],
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    document_ids_str = [str(document_id) for document_id in document_ids]
    query = select(DocumentModel).where(DocumentModel.id.in_(document_ids_str))
    if is_deleted:
        query = query.where(DocumentModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_documents = await db.execute(query)
    return db_documents.unique().scalars().all()


async def read_document(
    db: AsyncSession,
    document_id: UUID4,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    if update_lock:
        # update_lock이 True일 때는 JOIN 없이 document만 조회
        query = select(DocumentModel).where(
            DocumentModel.id == str(document_id)
        )
        if is_deleted is not None:
            query = query.where(DocumentModel.is_deleted.is_(is_deleted))
        query = query.with_for_update()
        db_document = await db.execute(query)
        return db_document.scalars().first()
    else:
        # 일반 조회 시에는 JOIN과 eager loading 사용
        query = (
            (
                select(DocumentModel).outerjoin(
                    ChunkModel,
                    and_(
                        DocumentModel.id == ChunkModel.document_id,
                        or_(
                            ChunkModel.is_deleted.is_(
                                False
                            ),  # ON 조건에서 필터링
                            ChunkModel.id.is_(None),
                        ),
                    ),
                )
            )
            .where(and_(DocumentModel.id == str(document_id)))
            .options(contains_eager(DocumentModel.chunks))
        )
        if is_deleted is not None:
            query = query.where(DocumentModel.is_deleted.is_(is_deleted))
        db_document = await db.execute(query)
        return db_document.unique().scalars().first()


async def read_document_by_email(
    db: AsyncSession,
    email: str,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    query = select(DocumentModel).where(
        and_(
            DocumentModel.email == email,
            DocumentModel.is_deleted.is_(False),
        )
    )
    if is_deleted:
        query = query.where(DocumentModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_document = await db.execute(query)
    return db_document.unique().scalars().first()


async def read_document_by_document_number(
    db: AsyncSession,
    document_number: str,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    query = select(DocumentModel).where(
        and_(
            DocumentModel.document_number == document_number,
            DocumentModel.is_deleted.is_(False),
        )
    )
    if is_deleted:
        query = query.where(DocumentModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_document = await db.execute(query)
    return db_document.unique().scalars().first()


async def update_document(
    db_document: DocumentModel,
    document: DocumentUpdateRequest,
    updated_by: Optional[UUID4] = None,
):
    # 각 필드를 동적으로 업데이트
    for key, value in document.model_dump(exclude_unset=True).items():
        if hasattr(
            db_document, key
        ):  # DocumentModel에 해당 필드가 있는지 확인
            setattr(db_document, key, value)
    db_document.updated_at = datetime.datetime.now()
    db_document.updated_by = (
        updated_by if updated_by else db_document.updated_by
    )
    return db_document


async def delete_document(
    db_document: DocumentModel,
    updated_by: Optional[UUID4] = None,
):
    if not db_document:
        return None

    db_document.is_deleted = True
    db_document.updated_at = datetime.datetime.now()
    db_document.updated_by = (
        updated_by if updated_by else db_document.updated_by
    )

    return db_document


async def delete_document_hard(
    db_document: DocumentModel,
    db: AsyncSession,
):
    if not db_document:
        return None

    await db.delete(db_document)

    return db_document
