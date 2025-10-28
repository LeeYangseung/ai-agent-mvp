from app.core.exception import (
    NotFoundError,
    InternalServerError,
    CustomException,
    BadRequestError,
)
from app.database.crud.graph import edge as edge_crud
from app.schemas.graph.edge import (
    EdgeDetail,
    EdgeResponse,
    EdgesResponse,
    EdgeCreateRequest,
    EdgeUpdateRequest,
    EdgeDeleteRequest,
    EdgeIdResponse,
)
from app.schemas.pagination import Pagination
from app.utils.common import convert_sqlalchemy_to_pydantic
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4
from uuid import UUID

"""
여기에 Edge 서비스 함수를 구현합니다.
서비스 레이어에는 아래와 같은 역할을 합니다.
    - 비즈니스 로직 구현
    - 데이터 유효성 검사
    - crud 상태를 보고 적절한 커스텀 에러 raise
    - 트랜잭션 관리(db commit, rollback)
    - sqlalchemy 객체를 pydantic model로 validation
    - API의 전체 로직 흐름 제어
"""


async def get_edges(
    db: AsyncSession,
    page: int = 0,
    size: int = 10,
    edge_id: Optional[UUID4] = None,
    graph_id: Optional[UUID4] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
    sort: Optional[str] = "created_at:desc",
):
    """
    엣지 목록과 페이징 데이터를 조합하는 서비스 함수
    """
    try:
        # size None일 시 전체 목록 조회
        skip, limit = (0, None) if size is None else (page * size, size)

        # 엣지 목록과 전체 엣지 수 조회
        total_count, db_edges = await edge_crud.read_edges(
            db,
            skip=skip,
            limit=limit,
            edge_id=edge_id,
            graph_id=graph_id,
            source=source,
            target=target,
            sort=sort,
        )

        # Pagination 객체 생성 (utils의 Pagination 사용하여 0으로 나누기 문제 해결)
        pagination = Pagination.create(
            total_count=total_count or 0,
            current_page=page,
            page_size=size if size is not None else (total_count or 0),
        )

        # 엣지 데이터 변환
        edges = [
            convert_sqlalchemy_to_pydantic(edge, EdgeDetail)
            for edge in db_edges
        ]

        # 최종 응답 반환
        return pagination, EdgesResponse(edges=edges)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def get_edge(
    db: AsyncSession,
    edge_id: UUID4,
) -> EdgeResponse:
    """
    엣지 데이터를 가져오는 서비스 함수
    """
    try:
        db_edge = await edge_crud.read_edge(
            db=db,
            edge_id=edge_id,
            is_deleted=False,
        )
        if db_edge is None:
            raise NotFoundError()

        # SQLAlchemy 객체를 Pydantic 모델로 변환
        edge_detail = convert_sqlalchemy_to_pydantic(db_edge, EdgeDetail)

        return EdgeResponse(edge=edge_detail)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def create_edge(
    db: AsyncSession,
    edge: EdgeCreateRequest,
) -> EdgeIdResponse:
    """
    엣지 데이터를 생성하는 서비스 함수
    """
    try:
        if edge.graph_id is None:
            raise BadRequestError(data="graph_id is required")
        db_edge = await edge_crud.create_edge(
            db=db,
            edge=edge,
        )
        await db.commit()
        await db.refresh(db_edge)
        return EdgeIdResponse(id=UUID(str(db_edge.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def update_edge(
    db: AsyncSession,
    edge_id: UUID4,
    edge: EdgeUpdateRequest,
) -> EdgeIdResponse:
    """
    엣지 데이터를 수정하는 서비스 함수
    """
    try:
        db_edge = await edge_crud.read_edge(
            db=db,
            edge_id=edge_id,
            update_lock=True,
            is_deleted=False,
        )
        if db_edge is None:
            raise NotFoundError()

        db_edge = await edge_crud.update_edge(
            db_edge=db_edge,
            edge=edge,
        )
        await db.commit()
        await db.refresh(db_edge)
        return EdgeIdResponse(id=UUID(str(db_edge.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_edge(
    db: AsyncSession,
    edge_id: UUID4,
    edge: EdgeDeleteRequest,
) -> EdgeIdResponse:
    """
    엣지 데이터를 삭제하는 서비스 함수
    """
    try:
        db_edge = await edge_crud.read_edge(
            db=db,
            edge_id=edge_id,
            update_lock=True,
            is_deleted=False,
        )
        if db_edge is None:
            raise NotFoundError()
        db_edge = await edge_crud.delete_edge(
            db_edge=db_edge,
            updated_by=edge.updated_by,
        )
        await db.commit()
        await db.refresh(db_edge)
        return EdgeIdResponse(id=UUID(str(db_edge.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_edge_hard(
    db: AsyncSession,
    edge_id: UUID4,
    edge: EdgeDeleteRequest,
) -> EdgeIdResponse:
    """
    엣지 데이터를 하드 삭제하는 서비스 함수
    """
    try:
        db_edge = await edge_crud.read_edge(
            db=db,
            edge_id=edge_id,
            update_lock=True,
        )
        if db_edge is None:
            raise NotFoundError()
        db_edge = await edge_crud.delete_edge_hard(
            db_edge=db_edge,
            db=db,
        )
        await db.commit()
        await db.refresh(db_edge)
        return EdgeIdResponse(id=UUID(str(db_edge.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))
