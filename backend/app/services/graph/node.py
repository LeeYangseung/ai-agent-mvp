from app.core.exception import (
    NotFoundError,
    InternalServerError,
    CustomException,
    BadRequestError,
    ConflictError,
)
from app.database.crud.graph import node as node_crud
from app.schemas.graph.node import (
    NodeDetail,
    NodeResponse,
    NodesResponse,
    NodeCreateRequest,
    NodeUpdateRequest,
    NodeDeleteRequest,
    NodeIdResponse,
)
from app.schemas.pagination import Pagination
from app.utils.common import convert_sqlalchemy_to_pydantic
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4
from uuid import UUID

"""
여기에 Node 서비스 함수를 구현합니다.
서비스 레이어에는 아래와 같은 역할을 합니다.
    - 비즈니스 로직 구현
    - 데이터 유효성 검사
    - crud 상태를 보고 적절한 커스텀 에러 raise
    - 트랜잭션 관리(db commit, rollback)
    - sqlalchemy 객체를 pydantic model로 validation
    - API의 전체 로직 흐름 제어
"""


async def get_nodes(
    db: AsyncSession,
    page: int = 0,
    size: int = 10,
    node_uuid: Optional[UUID4] = None,
    graph_id: Optional[UUID4] = None,
    node_id: Optional[str] = None,
    type: Optional[str] = None,
    order: Optional[int] = None,
    sort: Optional[str] = "created_at:desc",
):
    """
    노드 목록과 페이징 데이터를 조합하는 서비스 함수
    """
    try:
        # size None일 시 전체 목록 조회
        skip, limit = (0, None) if size is None else (page * size, size)

        # 노드 목록과 전체 노드 수 조회
        total_count, db_nodes = await node_crud.read_nodes(
            db,
            skip=skip,
            limit=limit,
            node_uuid=node_uuid,
            graph_id=graph_id,
            node_id=node_id,
            type=type,
            order=order,
            sort=sort,
        )

        # Pagination 객체 생성 (utils의 Pagination 사용하여 0으로 나누기 문제 해결)
        pagination = Pagination.create(
            total_count=total_count or 0,
            current_page=page,
            page_size=size if size is not None else (total_count or 0),
        )

        # 노드 데이터 변환
        nodes = [
            convert_sqlalchemy_to_pydantic(node, NodeDetail)
            for node in db_nodes
        ]

        # 최종 응답 반환
        return pagination, NodesResponse(nodes=nodes)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def get_node(
    db: AsyncSession,
    node_uuid: UUID4,
) -> NodeResponse:
    """
    노드 데이터를 가져오는 서비스 함수
    """
    try:
        db_node = await node_crud.read_node(
            db=db,
            node_uuid=node_uuid,
            is_deleted=False,
        )
        if db_node is None:
            raise NotFoundError()

        # SQLAlchemy 객체를 Pydantic 모델로 변환
        node_detail = convert_sqlalchemy_to_pydantic(db_node, NodeDetail)

        return NodeResponse(node=node_detail)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def create_node(
    db: AsyncSession,
    node: NodeCreateRequest,
) -> NodeIdResponse:
    """
    노드 데이터를 생성하는 서비스 함수
    """
    try:
        # 입력 값 검증
        if node.graph_id is None:
            raise BadRequestError(data="graph_id is required")

        # 중복 노드 검증
        existing_nodes = await node_crud.read_nodes(
            db,
            node_id=node.node_id,
            graph_id=node.graph_id,
            limit=None,
        )
        if existing_nodes[1]:
            raise ConflictError(data="node already exists")

        # 노드 생성
        db_node = await node_crud.create_node(
            db,
            node=node,
        )
        await db.commit()
        await db.refresh(db_node)
        return NodeIdResponse(id=UUID(str(db_node.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def update_node(
    db: AsyncSession,
    node_uuid: UUID4,
    node: NodeUpdateRequest,
) -> NodeIdResponse:
    """
    노드 데이터를 수정하는 서비스 함수
    """
    try:
        db_node = await node_crud.read_node(
            db,
            node_uuid=node_uuid,
            update_lock=True,
            is_deleted=False,
        )
        if db_node is None:
            raise NotFoundError()

        db_node = await node_crud.update_node(
            db_node=db_node,
            node=node,
        )
        await db.commit()
        await db.refresh(db_node)
        return NodeIdResponse(id=UUID(str(db_node.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_node(
    db: AsyncSession,
    node_uuid: UUID4,
    node: NodeDeleteRequest,
) -> NodeIdResponse:
    """
    노드 데이터를 삭제하는 서비스 함수
    """
    try:
        db_node = await node_crud.read_node(
            db,
            node_uuid=node_uuid,
            update_lock=True,
            is_deleted=False,
        )
        if db_node is None:
            raise NotFoundError()
        db_node = await node_crud.delete_node(
            db_node=db_node,
            updated_by=node.updated_by,
        )
        await db.commit()
        await db.refresh(db_node)
        return NodeIdResponse(id=UUID(str(db_node.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_node_hard(
    db: AsyncSession,
    node_uuid: UUID4,
) -> NodeIdResponse:
    """
    노드 데이터를 하드 삭제하는 서비스 함수
    """
    try:
        db_node = await node_crud.read_node(
            db=db,
            node_uuid=node_uuid,
            update_lock=True,
        )
        if db_node is None:
            raise NotFoundError()
        db_node = await node_crud.delete_node_hard(
            db_node=db_node,
            db=db,
        )
        await db.commit()
        await db.refresh(db_node)
        return NodeIdResponse(id=UUID(str(db_node.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))
