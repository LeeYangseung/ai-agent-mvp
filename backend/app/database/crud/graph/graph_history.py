from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from pydantic import UUID4
from typing import List, Optional, Sequence
import datetime

from app.database.models.graph.graph_history import (
    GraphHistory as GraphHistoryModel,
)
from app.schemas.graph.graph_history import (
    GraphHistoryCreateRequest,
    GraphHistoryUpdateRequest,
)
from app.database.models.base import generate_uuid
from app.utils.common import parse_sort_conditions

"""
여기에 GraphHistory CRUD 함수를 구현합니다.
CRUD 함수에는 아래와 같은 역할을 합니다.
    - 데이터베이스 조회, 생성, 수정, 삭제 작업 수행
    - 데이터 존재 시 sqlalchemy 객체 반환, 데이터가 존재하지 않을 때는 None을 반환
CRUD 함수에서는 다음과 같은 처리를 하지 않아야 합니다.
    - db commit, rollback
    - 존재 여부, 데이터 유효성 판단 등 비즈니스 관점의 예외 처리
"""


async def create_graph_history(
    db: AsyncSession,
    graph_history: GraphHistoryCreateRequest,
    created_by: Optional[UUID4] = None,
):
    """GraphHistory 생성(INSERT)"""
    db_graph_history = GraphHistoryModel(
        id=str(generate_uuid()),
        graph_id=str(graph_history.graph_id),
        input_state=graph_history.input_state,
        output_state=graph_history.output_state,
        status=graph_history.status,
        error_message=graph_history.error_message,
        is_deleted=False,
        created_at=datetime.datetime.now(),
        created_by=created_by if created_by else graph_history.created_by,
        updated_at=datetime.datetime.now(),
        updated_by=created_by if created_by else graph_history.created_by,
    )
    db.add(db_graph_history)
    return db_graph_history


async def read_graph_histories(
    db: AsyncSession,
    skip: int = 0,
    limit: Optional[int] = 10,
    graph_history_id: Optional[UUID4] = None,
    graph_id: Optional[UUID4] = None,
    status: Optional[str] = None,
    sort: Optional[str] = None,
):
    query = select(GraphHistoryModel).where(
        GraphHistoryModel.is_deleted.is_(False)
    )

    # Filter 적용
    filter_conditions = []
    if graph_history_id:
        filter_conditions.append(GraphHistoryModel.id == str(graph_history_id))
    if graph_id:
        filter_conditions.append(GraphHistoryModel.graph_id == str(graph_id))
    if status:
        filter_conditions.append(GraphHistoryModel.status == status)
    if filter_conditions:
        query = query.where(and_(*filter_conditions))

    # Search 적용
    search_conditions = []
    if search_conditions:
        query = query.where(or_(*search_conditions))

    # total_count를 위한 쿼리
    total_count_query = select(func.count()).select_from(GraphHistoryModel)
    if query.whereclause is not None:
        total_count_query = total_count_query.where(query.whereclause)

    # Order 적용
    order_conditions = []
    if sort:
        order_conditions = parse_sort_conditions(sort, GraphHistoryModel)
        query = query.order_by(*order_conditions)

    # Pagination 적용
    if limit:
        query = query.offset(skip).limit(limit)

    db_graph_histories = await db.execute(query)
    total_count = await db.scalar(total_count_query)
    return total_count, db_graph_histories.scalars().all()


async def read_graph_histories_by_graph_history_ids(
    db: AsyncSession,
    graph_history_ids: List[UUID4],
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    graph_history_ids_str = [
        str(graph_history_id) for graph_history_id in graph_history_ids
    ]
    query = select(GraphHistoryModel).where(
        GraphHistoryModel.id.in_(graph_history_ids_str)
    )
    if is_deleted is not None:
        query = query.where(GraphHistoryModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_graph_histories = await db.execute(query)
    return db_graph_histories.unique().scalars().all()


async def read_graph_history(
    db: AsyncSession,
    graph_history_id: UUID4,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    query = select(GraphHistoryModel).where(
        GraphHistoryModel.id == str(graph_history_id)
    )
    if is_deleted is not None:
        query = query.where(GraphHistoryModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_graph_history = await db.execute(query)
    return db_graph_history.unique().scalars().first()


async def update_graph_history(
    db_graph_history: GraphHistoryModel,
    graph_history: GraphHistoryUpdateRequest,
    updated_by: Optional[UUID4] = None,
):
    for key, value in graph_history.model_dump(exclude_unset=True).items():
        if (
            hasattr(db_graph_history, key) and value is not None
        ):  # GraphHistoryModel에 해당 필드가 있는지 확인
            setattr(db_graph_history, key, value)
    db_graph_history.updated_at = datetime.datetime.now()
    db_graph_history.updated_by = (
        updated_by if updated_by else db_graph_history.updated_by
    )
    return db_graph_history


async def delete_graph_history(
    db_graph_history: GraphHistoryModel,
    updated_by: Optional[UUID4] = None,
):
    if not db_graph_history:
        return None

    db_graph_history.is_deleted = True
    db_graph_history.updated_at = datetime.datetime.now()
    db_graph_history.updated_by = (
        updated_by if updated_by else db_graph_history.updated_by
    )

    return db_graph_history


async def delete_graph_history_hard(
    db_graph_history: GraphHistoryModel,
    db: AsyncSession,
):
    if not db_graph_history:
        return None

    await db.delete(db_graph_history)

    return db_graph_history
