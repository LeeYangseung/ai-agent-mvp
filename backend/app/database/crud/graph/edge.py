from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from pydantic import UUID4
from typing import List, Optional, Sequence
import datetime

from app.database.models.graph.edge import Edge as EdgeModel
from app.schemas.graph.edge import EdgeCreateRequest, EdgeUpdateRequest
from app.database.models.base import generate_uuid
from app.utils.common import parse_sort_conditions

"""
여기에 Edge CRUD 함수를 구현합니다.
CRUD 함수에는 아래와 같은 역할을 합니다.
    - 데이터베이스 조회, 생성, 수정, 삭제 작업 수행
    - 데이터 존재 시 sqlalchemy 객체 반환, 데이터가 존재하지 않을 때는 None을 반환
CRUD 함수에서는 다음과 같은 처리를 하지 않아야 합니다.
    - db commit, rollback
    - 존재 여부, 데이터 유효성 판단 등 비즈니스 관점의 예외 처리
"""


async def create_edge(
    db: AsyncSession,
    edge: EdgeCreateRequest,
    created_by: Optional[UUID4] = None,
):
    """Edge 생성(INSERT)"""
    db_edge = EdgeModel(
        id=str(generate_uuid()),
        graph_id=str(edge.graph_id),
        source=edge.source,
        target=edge.target,
        condition=edge.condition,
        is_deleted=False,
        created_at=datetime.datetime.now(),
        created_by=created_by if created_by else edge.created_by,
        updated_at=datetime.datetime.now(),
        updated_by=created_by if created_by else edge.created_by,
    )
    db.add(db_edge)
    return db_edge


async def read_edges(
    db: AsyncSession,
    skip: int = 0,
    limit: Optional[int] = 10,
    edge_id: Optional[UUID4] = None,
    graph_id: Optional[UUID4] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
    sort: Optional[str] = None,
):
    query = select(EdgeModel).where(EdgeModel.is_deleted.is_(False))

    # Filter 적용
    filter_conditions = []
    if edge_id:
        filter_conditions.append(EdgeModel.id == str(edge_id))
    if graph_id:
        filter_conditions.append(EdgeModel.graph_id == str(graph_id))
    if source:
        filter_conditions.append(EdgeModel.source == source)
    if target:
        filter_conditions.append(EdgeModel.target == target)
    if filter_conditions:
        query = query.where(and_(*filter_conditions))

    # Search 적용
    search_conditions = []
    if search_conditions:
        query = query.where(or_(*search_conditions))

    # total_count를 위한 쿼리
    total_count_query = select(func.count()).select_from(EdgeModel)
    if query.whereclause is not None:
        total_count_query = total_count_query.where(query.whereclause)

    # Order 적용
    order_conditions = []
    if sort:
        order_conditions = parse_sort_conditions(sort, EdgeModel)
        query = query.order_by(*order_conditions)

    # Pagination 적용
    if limit:
        query = query.offset(skip).limit(limit)

    db_edges = await db.execute(query)
    total_count = await db.scalar(total_count_query)
    return total_count, db_edges.scalars().all()


async def read_edges_by_edge_ids(
    db: AsyncSession,
    edge_ids: List[UUID4],
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    edge_ids_str = [str(edge_id) for edge_id in edge_ids]
    query = select(EdgeModel).where(EdgeModel.id.in_(edge_ids_str))
    if is_deleted is not None:
        query = query.where(EdgeModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_edges = await db.execute(query)
    return db_edges.unique().scalars().all()


async def read_edge(
    db: AsyncSession,
    edge_id: UUID4,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    query = select(EdgeModel).where(EdgeModel.id == str(edge_id))
    if is_deleted is not None:
        query = query.where(EdgeModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_edge = await db.execute(query)
    return db_edge.unique().scalars().first()


async def update_edge(
    db_edge: EdgeModel,
    edge: EdgeUpdateRequest,
    updated_by: Optional[UUID4] = None,
):
    for key, value in edge.model_dump(exclude_unset=True).items():
        if (
            hasattr(db_edge, key) and value is not None
        ):  # EdgeModel에 해당 필드가 있는지 확인
            setattr(db_edge, key, value)
    db_edge.updated_at = datetime.datetime.now()
    db_edge.updated_by = updated_by if updated_by else db_edge.updated_by
    return db_edge


async def delete_edge(
    db_edge: EdgeModel,
    updated_by: Optional[UUID4] = None,
):
    if not db_edge:
        return None

    db_edge.is_deleted = True
    db_edge.updated_at = datetime.datetime.now()
    db_edge.updated_by = updated_by if updated_by else db_edge.updated_by

    return db_edge


async def delete_edge_hard(
    db_edge: EdgeModel,
    db: AsyncSession,
):
    if not db_edge:
        return None

    await db.delete(db_edge)

    return db_edge
