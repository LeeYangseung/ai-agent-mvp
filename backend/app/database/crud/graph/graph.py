import datetime
from typing import List, Optional, Sequence
from pydantic import UUID4
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.database.models.graph.graph import Graph as GraphModel
from app.database.models.graph.node import Node as NodeModel
from app.database.models.graph.edge import Edge as EdgeModel
from app.database.models.graph.graph_history import (
    GraphHistory as GraphHistoryModel,
)
from app.schemas.graph.graph import (
    GraphCreateRequest,
    GraphUpdateRequest,
)
from app.database.models.base import generate_uuid
from app.utils.common import parse_sort_conditions


"""
여기에 Graph CRUD 함수를 구현합니다.
CRUD 함수에는 아래와 같은 역할을 합니다.
    - 데이터베이스 조회, 생성, 수정, 삭제 작업 수행
    - 데이터 존재 시 sqlalchemy 객체 반환, 데이터가 존재하지 않을 때는 None을 반환
CRUD 함수에서는 다음과 같은 처리를 하지 않아야 합니다.
    - db commit, rollback
    - 존재 여부, 데이터 유효성 판단 등 비즈니스 관점의 예외 처리
"""


async def create_graph(
    db: AsyncSession,
    graph: GraphCreateRequest,
    created_by: Optional[UUID4] = None,
):
    db_graph = GraphModel(
        id=str(generate_uuid()),
        name=graph.name,
        description=graph.description,
        version=graph.version,
        is_deleted=False,
        created_at=datetime.datetime.now(),
        created_by=created_by if created_by else graph.created_by,
        updated_at=datetime.datetime.now(),
        updated_by=created_by if created_by else graph.created_by,
    )
    db.add(db_graph)
    return db_graph


async def read_graphs(
    db: AsyncSession,
    skip: int = 0,
    limit: Optional[int] = None,
    graph_id: Optional[UUID4] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[int] = None,
    sort: Optional[str] = None,
):
    # 쿼리에 Join이 들어가는 경우 search, filter, order, offset, limit의 정합성을 보장하기 위해
    # base_query로 조건에 해당하는 id값을 찾고, 해당 id를 기반으로 Main 쿼리 실행
    # 공통 조인 조건을 적용하는 헬퍼 함수
    def apply_common_joins(query):
        return (
            query.outerjoin(
                NodeModel,
                and_(
                    GraphModel.id == NodeModel.graph_id,
                    or_(
                        NodeModel.is_deleted.is_(False),  # ON 조건에서 필터링
                        NodeModel.id.is_(None),
                    ),
                ),
            )
            .outerjoin(
                EdgeModel,
                and_(
                    GraphModel.id == EdgeModel.graph_id,
                    or_(
                        EdgeModel.is_deleted.is_(False),  # ON 조건에서 필터링
                        EdgeModel.id.is_(None),
                    ),
                ),
            )
            .outerjoin(
                GraphHistoryModel,
                and_(
                    GraphModel.id == GraphHistoryModel.graph_id,
                    or_(
                        GraphHistoryModel.is_deleted.is_(
                            False
                        ),  # ON 조건에서 필터링
                        GraphHistoryModel.id.is_(None),
                    ),
                ),
            )
            .where(GraphModel.is_deleted.is_(False))
        )

    # 1. 먼저 Graph.id를 기준으로 서브쿼리를 생성하여 필터, 검색, 정렬 및 페이징을 적용
    base_query = select(
        GraphModel.id,
    ).select_from(GraphModel)

    base_query = apply_common_joins(base_query)

    # Filter 적용
    filter_conditions = []

    if graph_id:
        filter_conditions.append(GraphModel.id == str(graph_id))
    if version:
        filter_conditions.append(GraphModel.version == version)
    if filter_conditions:
        base_query = base_query.where(and_(*filter_conditions))

    # Search 적용
    search_conditions = []

    if name:
        search_conditions.append(GraphModel.name.ilike(f"%{name}%"))
    if description:
        search_conditions.append(
            GraphModel.description.ilike(f"%{description}%")
        )
    if search_conditions:
        base_query = base_query.where(or_(*search_conditions))

    # order 적용
    order_conditions = []
    if sort:
        order_conditions = parse_sort_conditions(sort, GraphModel)
        # DISTINCT ON을 사용할 때는 첫 번째 ORDER BY 컬럼이 DISTINCT ON 컬럼과 일치해야 함
        # graph.id를 먼저 추가하고, 그 다음에 원래 정렬 조건을 추가
        base_query = base_query.order_by(GraphModel.id, *order_conditions)
    else:
        # sort가 없을 때는 기본적으로 graph.id로 정렬
        base_query = base_query.order_by(GraphModel.id)

    # Graph.id로 distinct 적용
    base_query = base_query.distinct(GraphModel.id)

    # total_count_query는 이 서브쿼리를 기반으로 전체 개수를 계산
    total_count_query = select(func.count()).select_from(base_query.subquery())

    # Pagination 적용
    if limit:
        base_query = base_query.offset(skip).limit(limit)

    graph_ids_result = await db.execute(base_query)
    graph_ids = [row[0] for row in graph_ids_result.all()]

    # 2. 메인 쿼리: Graph 데이터를 조회하고 관계 데이터를 eager 로딩
    main_query = select(GraphModel).select_from(GraphModel)
    main_query = apply_common_joins(main_query)
    main_query = main_query.where(GraphModel.id.in_(graph_ids))

    # 정렬 조건은 서브쿼리와 동일하게 적용
    if sort:
        order_conditions = parse_sort_conditions(sort, GraphModel)
        main_query = main_query.order_by(*order_conditions)
    else:
        # 기본 정렬: created_at desc
        main_query = main_query.order_by(GraphModel.created_at.desc())
    main_query = main_query.options(
        contains_eager(GraphModel.nodes),
        contains_eager(GraphModel.edges),
        contains_eager(GraphModel.graph_histories),
    )

    db_graph = await db.execute(main_query)
    total_count = await db.scalar(total_count_query)
    return total_count, db_graph.unique().scalars().all()


async def read_graphs_by_graph_ids(
    db: AsyncSession,
    graph_ids: List[UUID4],
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    graph_ids_str = [str(graph_id) for graph_id in graph_ids]
    query = select(GraphModel).where(GraphModel.id.in_(graph_ids_str))
    if is_deleted:
        query = query.where(GraphModel.is_deleted.is_(is_deleted))
    if update_lock:
        query = query.with_for_update()
    db_graphs = await db.execute(query)
    return db_graphs.unique().scalars().all()


async def read_graph(
    db: AsyncSession,
    graph_id: UUID4,
    update_lock: Optional[bool] = False,
    is_deleted: Optional[bool] = None,
):
    if update_lock:
        # update_lock이 True일 때는 JOIN 없이 graph만 조회
        query = select(GraphModel).where(GraphModel.id == str(graph_id))
        if is_deleted is not None:
            query = query.where(GraphModel.is_deleted.is_(is_deleted))
        query = query.with_for_update()
        db_graph = await db.execute(query)
        return db_graph.scalars().first()
    else:
        # 일반 조회 시에는 JOIN과 eager loading 사용
        query = (
            (
                select(GraphModel)
                .outerjoin(
                    NodeModel,
                    and_(
                        GraphModel.id == NodeModel.graph_id,
                        or_(
                            NodeModel.is_deleted.is_(
                                False
                            ),  # ON 조건에서 필터링
                            NodeModel.id.is_(None),
                        ),
                    ),
                )
                .outerjoin(
                    EdgeModel,
                    and_(
                        GraphModel.id == EdgeModel.graph_id,
                        or_(
                            EdgeModel.is_deleted.is_(
                                False
                            ),  # ON 조건에서 필터링
                            EdgeModel.id.is_(None),
                        ),
                    ),
                )
                .outerjoin(
                    GraphHistoryModel,
                    and_(
                        GraphModel.id == GraphHistoryModel.graph_id,
                        or_(
                            GraphHistoryModel.is_deleted.is_(
                                False
                            ),  # ON 조건에서 필터링
                            GraphHistoryModel.id.is_(None),
                        ),
                    ),
                )
            )
            .where(GraphModel.id == str(graph_id))
            .options(
                contains_eager(GraphModel.nodes),
                contains_eager(GraphModel.edges),
                contains_eager(GraphModel.graph_histories),
            )
        )
        if is_deleted is not None:
            query = query.where(GraphModel.is_deleted.is_(is_deleted))
        db_graph = await db.execute(query)
        return db_graph.unique().scalars().first()


async def update_graph(
    db_graph: GraphModel,
    graph: GraphUpdateRequest,
    updated_by: Optional[UUID4] = None,
):
    # 각 필드를 동적으로 업데이트
    for key, value in graph.model_dump(exclude_unset=True).items():
        if (
            hasattr(db_graph, key) and value is not None
        ):  # GraphModel에 해당 필드가 있는지 확인
            setattr(db_graph, key, value)
    db_graph.updated_at = datetime.datetime.now()
    db_graph.updated_by = updated_by if updated_by else db_graph.updated_by
    return db_graph


async def delete_graph(
    db_graph: GraphModel,
    updated_by: Optional[UUID4] = None,
):
    if not db_graph:
        return None

    db_graph.is_deleted = True
    db_graph.updated_at = datetime.datetime.now()
    db_graph.updated_by = updated_by if updated_by else db_graph.updated_by

    return db_graph


async def delete_graph_hard(
    db_graph: GraphModel,
    db: AsyncSession,
):
    if not db_graph:
        return None

    await db.delete(db_graph)

    return db_graph
