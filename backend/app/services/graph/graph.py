import os
from fastapi import UploadFile
from fastapi import status as http_status
from app.core.exception import (
    NotFoundError,
    ConflictError,
    InternalServerError,
    CustomException,
)
from app.database.crud.graph import graph as graph_crud
from app.database.crud.graph import node as node_crud
from app.database.crud.graph import edge as edge_crud
from app.database.crud.graph import graph_history as graph_history_crud
from app.schemas.graph.graph import (
    GraphDetail,
    GraphResponse,
    GraphsResponse,
    GraphCreateRequest,
    GraphUpdateRequest,
    GraphDeleteRequest,
    GraphIdResponse,
    GraphIdsResponse,
)
from app.schemas.graph.node import NodeCreateRequest, NodeDetail
from app.schemas.graph.edge import EdgeCreateRequest, EdgeDetail
from app.schemas.graph.graph_history import (
    GraphHistoryCreateRequest,
    GraphHistoryDetail,
)
from app.schemas.pagination import Pagination
from app.utils.common import convert_sqlalchemy_to_pydantic
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple
from pydantic import UUID4
from uuid import UUID
import shutil

"""
여기에 Graph 서비스 함수를 구현합니다.
서비스 레이어에는 아래와 같은 역할을 합니다.
    - 비즈니스 로직 구현
    - 데이터 유효성 검사
    - crud 상태를 보고 적절한 커스텀 에러 raise
    - 트랜잭션 관리(db commit, rollback)
    - sqlalchemy 객체를 pydantic model로 validation
    - API의 전체 로직 흐름 제어
"""


async def get_graphs(
    db: AsyncSession,
    page: int = 0,
    size: int = 10,
    graph_id: Optional[UUID4] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[int] = None,
    sort: Optional[str] = "created_at:desc",
) -> Tuple[Pagination, GraphsResponse]:
    """
    그래프 목록과 페이징 데이터를 조합하는 서비스 함수
    """
    try:
        # size None일 시 전체 목록 조회
        skip, limit = (0, None) if size is None else (page * size, size)

        # 그래프 목록과 전체 그래프 수 조회
        total_count, db_graphs = await graph_crud.read_graphs(
            db,
            skip=skip,
            limit=limit,
            graph_id=graph_id,
            name=name,
            description=description,
            version=version,
            sort=sort,
        )

        # Pagination 객체 생성 (utils의 Pagination 사용하여 0으로 나누기 문제 해결)
        pagination = Pagination.create(
            total_count=total_count or 0,
            current_page=page,
            page_size=size if size is not None else (total_count or 0),
        )

        # 그래프 데이터 변환
        graphs = []
        for graph in db_graphs:
            # nodes 변환
            nodes = [
                convert_sqlalchemy_to_pydantic(node, NodeDetail)
                for node in getattr(graph, "nodes", [])
            ]

            # edges 변환
            edges = [
                convert_sqlalchemy_to_pydantic(edge, EdgeDetail)
                for edge in getattr(graph, "edges", [])
            ]

            # graph_histories 변환
            graph_histories = [
                convert_sqlalchemy_to_pydantic(
                    graph_history, GraphHistoryDetail
                )
                for graph_history in getattr(graph, "graph_histories", [])
            ]

            # graph 변환 (nodes, edges, graph_histories 포함)
            graph_dict = convert_sqlalchemy_to_pydantic(
                graph,
                GraphDetail,
                additional_fields={
                    "nodes": nodes,
                    "edges": edges,
                    "graph_histories": graph_histories,
                },
            )
            graphs.append(graph_dict)

        # 최종 응답 반환
        return pagination, GraphsResponse(graphs=graphs)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def get_graph(
    db: AsyncSession,
    graph_id: UUID4,
) -> GraphResponse:
    """
    그래프 데이터를 가져오는 서비스 함수
    """
    try:
        db_graph = await graph_crud.read_graph(
            db,
            graph_id=graph_id,
            is_deleted=False,
        )
        if db_graph is None:
            raise NotFoundError()

        # nodes 변환
        nodes = [
            convert_sqlalchemy_to_pydantic(node, NodeDetail)
            for node in getattr(db_graph, "nodes", [])
        ]

        # edges 변환
        edges = [
            convert_sqlalchemy_to_pydantic(edge, EdgeDetail)
            for edge in getattr(db_graph, "edges", [])
        ]

        # graph 변환 (nodes, edges 포함)
        graph_dict = convert_sqlalchemy_to_pydantic(
            db_graph,
            GraphDetail,
            additional_fields={"nodes": nodes, "edges": edges},
        )

        return GraphResponse(graph=graph_dict)
    except CustomException:
        raise
    except Exception as e:
        raise InternalServerError(data=str(e))


async def create_graph(
    db: AsyncSession,
    graph: GraphCreateRequest,
) -> GraphIdResponse:
    """
    그래프 데이터를 생성하는 서비스 함수
    """
    try:
        # 그래프 생성
        db_graph = await graph_crud.create_graph(
            db,
            graph=graph,
        )

        # node 생성
        for node in graph.nodes:
            node_create_request = NodeCreateRequest(
                graph_id=UUID(str(db_graph.id)),
                node_id=node.node_id,
                type=node.type,
                params=node.params,
                output=node.output,
                position=node.position,
                order=node.order,
                created_by=graph.created_by,
                updated_by=graph.updated_by,
            )
            _ = await node_crud.create_node(
                db,
                node=node_create_request,
            )

        # edge 생성
        for edge in graph.edges:
            edge_create_request = EdgeCreateRequest(
                graph_id=UUID(str(db_graph.id)),
                source=edge.source,
                target=edge.target,
                condition=edge.condition,
                created_by=graph.created_by,
                updated_by=graph.updated_by,
            )
            _ = await edge_crud.create_edge(
                db,
                edge=edge_create_request,
            )

        # graph_history 생성
        for graph_history in graph.graph_histories:
            graph_history_create_request = GraphHistoryCreateRequest(
                graph_id=UUID(str(db_graph.id)),
                input_state=graph_history.input_state,
                output_state=graph_history.output_state,
                status=graph_history.status,
                error_message=graph_history.error_message,
                created_by=graph.created_by,
                updated_by=graph.updated_by,
            )
            _ = await graph_history_crud.create_graph_history(
                db,
                graph_history=graph_history_create_request,
            )
        await db.commit()
        await db.refresh(db_graph)

        return GraphIdResponse(id=UUID(str(db_graph.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def update_graph(
    db: AsyncSession,
    graph_id: UUID4,
    graph: GraphUpdateRequest,
) -> GraphIdResponse:
    """
    그래프 데이터를 수정하는 서비스 함수
    """
    try:
        db_graph = await graph_crud.read_graph(
            db,
            graph_id=graph_id,
            update_lock=True,
            is_deleted=False,
        )
        if db_graph is None:
            raise NotFoundError()

        # nodes 정보를 별도로 저장
        nodes_data = getattr(graph, "nodes", None)
        # edges 정보를 별도로 저장
        edges_data = getattr(graph, "edges", None)
        # graph_histories 정보를 별도로 저장
        graph_histories_data = getattr(graph, "graph_histories", None)
        # nodes, edges, graph_histories를 제외한 graph 객체 생성
        graph_dict = graph.model_dump(
            exclude={"nodes", "edges", "graph_histories"}, exclude_unset=True
        )
        graph_without_nodes_edges_graph_histories = GraphUpdateRequest(
            **graph_dict
        )

        db_graph = await graph_crud.update_graph(
            db_graph=db_graph,
            graph=graph_without_nodes_edges_graph_histories,
        )

        # nodes가 있으면 기존 node들 삭제 후 새로운 node들 생성
        if nodes_data:
            # 기존 node들 조회 및 삭제
            existing_nodes = await node_crud.read_nodes(
                db,
                graph_id=UUID(str(db_graph.id)),
                limit=None,  # 모든 nodes 조회
            )
            if existing_nodes[1]:  # nodes가 있으면
                for node in existing_nodes[1]:
                    _ = await node_crud.delete_node(
                        db_node=node,
                    )

            # 새로운 node들 생성
            for node_data in nodes_data:
                node_create_request = NodeCreateRequest(
                    graph_id=UUID(str(db_graph.id)),
                    node_id=node_data.node_id,
                    type=node_data.type,
                    params=node_data.params,
                    output=node_data.output,
                    position=node_data.position,
                    order=node_data.order,
                    created_by=graph.updated_by,
                    updated_by=graph.updated_by,
                )
                _ = await node_crud.create_node(
                    db,
                    node=node_create_request,
                )

        # edges가 있으면 기존 edges들 삭제 후 새로운 edges들 생성
        if edges_data:
            # 기존 edges들 조회 및 삭제
            existing_edges = await edge_crud.read_edges(
                db,
                graph_id=UUID(str(db_graph.id)),
                limit=None,  # 모든 edges 조회
            )
            if existing_edges[1]:  # edges가 있으면
                for edge in existing_edges[1]:
                    _ = await edge_crud.delete_edge(
                        db_edge=edge,
                    )

            # 새로운 edges들 생성
            for edge_data in edges_data:
                edge_create_request = EdgeCreateRequest(
                    graph_id=UUID(str(db_graph.id)),
                    source=edge_data.source,
                    target=edge_data.target,
                    condition=edge_data.condition,
                    created_by=graph.updated_by,
                    updated_by=graph.updated_by,
                )
                _ = await edge_crud.create_edge(
                    db,
                    edge=edge_create_request,
                )

        # graph_histories가 있으면 기존 graph_histories들 삭제 후 새로운 graph_histories들 생성
        if graph_histories_data:
            # 기존 graph_histories들 조회 및 삭제
            existing_graph_histories = (
                await graph_history_crud.read_graph_histories(
                    db,
                    graph_id=UUID(str(db_graph.id)),
                    limit=None,  # 모든 graph_histories 조회
                )
            )
            if existing_graph_histories[1]:  # graph_histories가 있으면
                for graph_history in existing_graph_histories[1]:
                    _ = await graph_history_crud.delete_graph_history(
                        db_graph_history=graph_history,
                        updated_by=graph.updated_by,
                    )

            # 새로운 graph_histories들 생성
            for graph_history_data in graph_histories_data:
                graph_history_create_request = GraphHistoryCreateRequest(
                    graph_id=UUID(str(db_graph.id)),
                    input_state=graph_history_data.input_state,
                    output_state=graph_history_data.output_state,
                    status=graph_history_data.status,
                    error_message=graph_history_data.error_message,
                    created_by=graph.updated_by,
                    updated_by=graph.updated_by,
                )
                _ = await graph_history_crud.create_graph_history(
                    db,
                    graph_history=graph_history_create_request,
                )
        await db.commit()
        await db.refresh(db_graph)
        return GraphIdResponse(id=UUID(str(db_graph.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_graph(
    db: AsyncSession,
    graph_id: UUID4,
    graph: GraphDeleteRequest,
) -> GraphIdResponse:
    """
    그래프 데이터를 삭제하는 서비스 함수
    """
    try:
        db_graph = await graph_crud.read_graph(
            db,
            graph_id=graph_id,
            update_lock=True,
            is_deleted=False,
        )
        if db_graph is None:
            raise NotFoundError()
        # nodes 삭제
        existing_nodes = await node_crud.read_nodes(
            db,
            graph_id=UUID(str(db_graph.id)),
            limit=None,  # 모든 nodes 조회
        )
        if existing_nodes[1]:  # nodes가 있으면
            for node in existing_nodes[1]:
                _ = await node_crud.delete_node(
                    db_node=node,
                )
        # edges 삭제
        existing_edges = await edge_crud.read_edges(
            db,
            graph_id=UUID(str(db_graph.id)),
            limit=None,  # 모든 edges 조회
        )
        if existing_edges[1]:  # edges가 있으면
            for edge in existing_edges[1]:
                _ = await edge_crud.delete_edge(
                    db_edge=edge,
                )
        # graph_histories 삭제
        existing_graph_histories = (
            await graph_history_crud.read_graph_histories(
                db,
                graph_id=UUID(str(db_graph.id)),
                limit=None,  # 모든 graph_histories 조회
            )
        )
        if existing_graph_histories[1]:  # graph_histories가 있으면
            for graph_history in existing_graph_histories[1]:
                _ = await graph_history_crud.delete_graph_history(
                    db_graph_history=graph_history,
                    updated_by=graph.updated_by,
                )
        # graph 삭제
        db_graph = await graph_crud.delete_graph(
            db_graph=db_graph,
            updated_by=graph.updated_by,
        )
        await db.commit()
        await db.refresh(db_graph)
        return GraphIdResponse(id=UUID(str(db_graph.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))


async def delete_graph_hard(
    db: AsyncSession,
    graph_id: UUID4,
) -> GraphIdResponse:
    """
    그래프 데이터를 삭제하는 서비스 함수
    """
    try:
        db_graph = await graph_crud.read_graph(
            db,
            graph_id=graph_id,
            update_lock=True,
        )
        if db_graph is None:
            raise NotFoundError()
        # nodes 삭제
        existing_nodes = await node_crud.read_nodes(
            db,
            graph_id=UUID(str(db_graph.id)),
            limit=None,  # 모든 nodes 조회
        )
        if existing_nodes[1]:  # nodes가 있으면
            for node in existing_nodes[1]:
                _ = await node_crud.delete_node_hard(
                    db_node=node,
                    db=db,
                )
        # edges 삭제
        existing_edges = await edge_crud.read_edges(
            db,
            graph_id=UUID(str(db_graph.id)),
            limit=None,  # 모든 edges 조회
        )
        if existing_edges[1]:  # edges가 있으면
            for edge in existing_edges[1]:
                _ = await edge_crud.delete_edge_hard(
                    db_edge=edge,
                    db=db,
                )
        # graph_histories 삭제
        existing_graph_histories = (
            await graph_history_crud.read_graph_histories(
                db,
                graph_id=UUID(str(db_graph.id)),
                limit=None,  # 모든 graph_histories 조회
            )
        )
        if existing_graph_histories[1]:  # graph_histories가 있으면
            for graph_history in existing_graph_histories[1]:
                _ = await graph_history_crud.delete_graph_history_hard(
                    db_graph_history=graph_history,
                    db=db,
                )
        # graph 삭제
        db_graph = await graph_crud.delete_graph_hard(
            db_graph=db_graph,
            db=db,
        )
        await db.commit()
        await db.refresh(db_graph)
        return GraphIdResponse(id=UUID(str(db_graph.id)))
    except CustomException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise InternalServerError(data=str(e))
