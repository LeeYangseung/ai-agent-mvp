from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from pydantic import UUID4
from typing import List, Optional, Sequence
import datetime

from app.database.models.graph.node import Node as NodeModel
from app.schemas.graph.node import NodeCreateRequest, NodeUpdateRequest
from app.database.models.base import generate_uuid
from app.utils.common import parse_sort_conditions

"""
여기에 Node CRUD 함수를 구현합니다.
CRUD 함수에는 아래와 같은 역할을 합니다.
    - 데이터베이스 조회, 생성, 수정, 삭제 작업 수행
    - 데이터 존재 시 sqlalchemy 객체 반환, 데이터가 존재하지 않을 때는 None을 반환
CRUD 함수에서는 다음과 같은 처리를 하지 않아야 합니다.
    - db commit, rollback
    - 존재 여부, 데이터 유효성 판단 등 비즈니스 관점의 예외 처리
"""


async def create_node(
    db: AsyncSession,
    node: NodeCreateRequest,
    created_by: Optional[UUID4] = None,
):
    """Node 생성(INSERT)"""
    db_node = NodeModel(
        id=str(generate_uuid()),
        graph_id=str(node.graph_id),
        node_id=node.node_id,
        type=node.type,
        params=node.params,
        output=node.output,
        position=node.position,
        order=node.order,
        is_deleted=False,
        created_by=created_by if created_by else node.created_by,
        updated_by=created_by if created_by else node.created_by,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    db.add(db_node)
    return db_node


async def read_nodes(
    db: AsyncSession,
    skip: int = 0,
    limit: Optional[int] = 10,
    node_uuid: Optional[UUID4] = None,
    graph_id: Optional[UUID4] = None,
    node_id: Optional[str] = None,
    type: Optional[str] = None,
    order: Optional[int] = None,
    sort: Optional[str] = None,
):
    query = select(NodeModel).where(NodeModel.is_deleted.is_(False))

    # Filter 적용
    filter_conditions = []
    if node_uuid:
        filter_conditions.append(NodeModel.id == str(node_uuid))
    if graph_id:
        filter_conditions.append(NodeModel.graph_id == str(graph_id))
    if type:
        filter_conditions.append(NodeModel.type == type)
    if order:
        filter_conditions.append(NodeModel.order == order)
    if filter_conditions:
        query = query.where(and_(*filter_conditions))

    # Search 적용
    search_conditions = []
    if node_id:
        search_conditions.append(NodeModel.node_id.ilike(f"%{node_id}%"))
    if search_conditions:
        query = query.where(or_(*search_conditions))

    # total_count를 위한 쿼리
    total_count_query = select(func.count()).select_from(NodeModel)
    if query.whereclause is not None:
        total_count_query = total_count_query.where(query.whereclause)

    # Order 적용
    order_conditions = []
    if sort:
        order_conditions = parse_sort_conditions(sort, NodeModel)
        query = query.order_by(*order_conditions)

    # Pagination 적용
    if limit:
        query = query.offset(skip).limit(limit)

    db_nodes = await db.execute(query)
    total_count = await db.scalar(total_count_query)
    return total_count, db_nodes.scalars().all()


async def read_nodes_by_node_ids(
    db: AsyncSession,
    node_uuids: List[UUID4],
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    node_uuids_str = [str(node_uuid) for node_uuid in node_uuids]
    query = select(NodeModel).where(NodeModel.id.in_(node_uuids_str))
    if is_deleted is not None:
        query = query.where(NodeModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_nodes = await db.execute(query)
    return db_nodes.unique().scalars().all()


async def read_node(
    db: AsyncSession,
    node_uuid: UUID4,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    query = select(NodeModel).where(NodeModel.id == str(node_uuid))
    if is_deleted is not None:
        query = query.where(NodeModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_node = await db.execute(query)
    return db_node.unique().scalars().first()


async def update_node(
    db_node: NodeModel,
    node: NodeUpdateRequest,
    updated_by: Optional[UUID4] = None,
):
    for key, value in node.model_dump(exclude_unset=True).items():
        if (
            hasattr(db_node, key) and value is not None
        ):  # NodeModel에 해당 필드가 있는지 확인
            setattr(db_node, key, value)
    db_node.updated_at = datetime.datetime.now()
    db_node.updated_by = updated_by if updated_by else db_node.updated_by
    return db_node


async def delete_node(
    db_node: NodeModel,
    updated_by: Optional[UUID4] = None,
):
    if not db_node:
        return None

    db_node.is_deleted = True
    db_node.updated_at = datetime.datetime.now()
    db_node.updated_by = updated_by if updated_by else db_node.updated_by

    return db_node


async def delete_node_hard(
    db_node: NodeModel,
    db: AsyncSession,
):
    if not db_node:
        return None

    await db.delete(db_node)

    return db_node
