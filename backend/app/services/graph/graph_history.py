from app.core.exception import (
    NotFoundError,
    InternalServerError,
    CustomException,
    BadRequestError,
)
from app.database.crud.graph import graph_history as graph_history_crud
from app.schemas.graph.graph_history import (
    GraphHistoryDetail,
    GraphHistoryResponse,
    GraphHistoriesResponse,
    GraphHistoryCreateRequest,
    GraphHistoryUpdateRequest,
    GraphHistoryDeleteRequest,
    GraphHistoryIdResponse,
)
from app.schemas.pagination import Pagination
from app.utils.common import convert_sqlalchemy_to_pydantic
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import UUID4
from uuid import UUID

"""
여기에 GraphHistory 서비스 함수를 구현합니다.
서비스 레이어에는 아래와 같은 역할을 합니다.
    - 비즈니스 로직 구현
    - 데이터 유효성 검사
    - crud 상태를 보고 적절한 커스텀 에러 raise
    - 트랜잭션 관리(db commit, rollback)
    - sqlalchemy 객체를 pydantic model로 validation
    - API의 전체 로직 흐름 제어
"""


async def get_graph_histories(
    db: AsyncSession,
    page: int = 0,
    size: int = 10,
    graph_history_id: Optional[UUID4] = None,
    graph_id: Optional[UUID4] = None,
    status: Optional[str] = None,
    sort: Optional[str] = "created_at:desc",
):
    """
    그래프 히스토리 목록과 페이징 데이터를 조합하는 서비스 함수
    """
    try:
        # size None일 시 전체 목록 조회
        skip, limit = (0, None) if size is None else (page * size, size)

        # 그래프 히스토리 목록과 전체 그래프 히스토리 수 조회
        total_count, db_graph_histories = (
            await graph_history_crud.read_graph_histories(
                db,
                skip=skip,
                limit=limit,
                graph_history_id=graph_history_id,
                graph_id=graph_id,
                status=status,
                sort=sort,
            )
        )

        # Pagination 객체 생성 (utils의 Pagination 사용하여 0으로 나누기 문제 해결)
        pagination = Pagination.create(
            total_count=total_count or 0,
            current_page=page,
            page_size=size if size is not None else (total_count or 0),
        )

        # 그래프 히스토리 데이터 변환
        graph_histories = [
            convert_sqlalchemy_to_pydantic(graph_history, GraphHistoryDetail)
            for graph_history in db_graph_histories
        ]

        # 최종 응답 반환
        return pagination, GraphHistoriesResponse(
            graph_histories=graph_histories
        )
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def get_graph_history(
    db: AsyncSession,
    graph_history_id: UUID4,
) -> GraphHistoryResponse:
    """
    그래프 히스토리 데이터를 가져오는 서비스 함수
    """
    try:
        db_graph_history = await graph_history_crud.read_graph_history(
            db=db,
            graph_history_id=graph_history_id,
            is_deleted=False,
        )
        if db_graph_history is None:
            raise NotFoundError()

        # SQLAlchemy 객체를 Pydantic 모델로 변환
        graph_history_detail = convert_sqlalchemy_to_pydantic(
            db_graph_history, GraphHistoryDetail
        )

        return GraphHistoryResponse(graph_history=graph_history_detail)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def create_graph_history(
    db: AsyncSession,
    graph_history: GraphHistoryCreateRequest,
) -> GraphHistoryIdResponse:
    """
    그래프 히스토리 데이터를 생성하는 서비스 함수
    """
    try:
        if graph_history.graph_id is None:
            raise BadRequestError(data="graph_id is required")
        db_graph_history = await graph_history_crud.create_graph_history(
            db=db,
            graph_history=graph_history,
        )
        await db.commit()
        await db.refresh(db_graph_history)
        return GraphHistoryIdResponse(id=UUID(str(db_graph_history.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def update_graph_history(
    db: AsyncSession,
    graph_history_id: UUID4,
    graph_history: GraphHistoryUpdateRequest,
) -> GraphHistoryIdResponse:
    """
    그래프 히스토리 데이터를 수정하는 서비스 함수
    """
    try:
        db_graph_history = await graph_history_crud.read_graph_history(
            db=db,
            graph_history_id=graph_history_id,
            update_lock=True,
            is_deleted=False,
        )
        if db_graph_history is None:
            raise NotFoundError()

        db_graph_history = await graph_history_crud.update_graph_history(
            db_graph_history=db_graph_history,
            graph_history=graph_history,
        )
        await db.commit()
        await db.refresh(db_graph_history)
        return GraphHistoryIdResponse(id=UUID(str(db_graph_history.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_graph_history(
    db: AsyncSession,
    graph_history_id: UUID4,
    graph_history: GraphHistoryDeleteRequest,
) -> GraphHistoryIdResponse:
    """
    그래프 히스토리 데이터를 삭제하는 서비스 함수
    """
    try:
        db_graph_history = await graph_history_crud.read_graph_history(
            db=db,
            graph_history_id=graph_history_id,
            update_lock=True,
            is_deleted=False,
        )
        if db_graph_history is None:
            raise NotFoundError()
        db_graph_history = await graph_history_crud.delete_graph_history(
            db_graph_history=db_graph_history,
            updated_by=graph_history.updated_by,
        )
        await db.commit()
        await db.refresh(db_graph_history)
        return GraphHistoryIdResponse(id=UUID(str(db_graph_history.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_graph_history_hard(
    db: AsyncSession,
    graph_history_id: UUID4,
) -> GraphHistoryIdResponse:
    """
    그래프 히스토리 데이터를 하드 삭제하는 서비스 함수
    """
    try:
        db_graph_history = await graph_history_crud.read_graph_history(
            db=db,
            graph_history_id=graph_history_id,
            update_lock=True,
        )
        if not db_graph_history:
            raise NotFoundError()
        db_graph_history = await graph_history_crud.delete_graph_history_hard(
            db_graph_history=db_graph_history,
            db=db,
        )
        await db.commit()
        await db.refresh(db_graph_history)
        return GraphHistoryIdResponse(id=UUID(str(db_graph_history.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))
