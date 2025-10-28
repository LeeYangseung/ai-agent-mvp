# app/schemas/graph/graph.py
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from typing import Dict, Any
from app.schemas.graph.node import (
    NodeCreateRequest,
    NodeDetail,
    NodeUpdateRequest,
)
from app.schemas.graph.edge import (
    EdgeCreateRequest,
    EdgeDetail,
    EdgeUpdateRequest,
)
from app.schemas.graph.graph_history import (
    GraphHistoryCreateRequest,
    GraphHistoryDetail,
    GraphHistoryUpdateRequest,
)


class GraphBase(BaseModel):
    name: str
    description: Optional[str] = None
    version: Optional[int] = 1


class GraphCreateRequest(GraphBase):
    nodes: Optional[List[NodeCreateRequest]] = Field(default=[])
    edges: Optional[List[EdgeCreateRequest]] = Field(default=[])
    graph_histories: Optional[List[GraphHistoryCreateRequest]] = Field(
        default=[]
    )
    created_by: Optional[str] = "admin"
    updated_by: Optional[str] = created_by
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = created_at

    class Config:
        json_schema_extra = {
            "example": {
                "name": "RAG 기반 검색 그래프",
                "description": "사용자 입력을 받아 문서 검색 후 답변 생성",
                "version": 1,
                "nodes": [
                    {
                        "node_id": "input-1",
                        "type": "InputNode",
                        "params": {},
                        "output": "user_input",
                    },
                    {
                        "node_id": "prompt-1",
                        "type": "PromptNode",
                        "params": {
                            "system_prompt": "You are an AI",
                            "user_prompt": "{user_input}",
                            "inputs": {
                                "user_input": {
                                    "type": "reference",
                                    "value": "input-1.output",
                                }
                            },
                        },
                        "output": "query",
                    },
                ],
                "edges": [
                    {
                        "source": "input-1",
                        "target": "prompt-1",
                        "condition": {"operator": "==", "value": "일번"},
                    }
                ],
                "created_by": "admin",
                "updated_by": "admin",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        }


class GraphUpdateRequest(GraphBase):
    nodes: Optional[List[NodeUpdateRequest]] = Field(default=[])
    edges: Optional[List[EdgeUpdateRequest]] = Field(default=[])
    graph_histories: Optional[List[GraphHistoryUpdateRequest]] = Field(
        default=[]
    )
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[int] = None
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "RAG 그래프 v2",
                "description": "ConditionNode 추가",
                "version": 2,
                "nodes": [
                    {
                        "node_id": "prompt-2",
                        "type": "PromptNode",
                        "params": {
                            "system_prompt": "You are an AI",
                            "user_prompt": "{user_input}",
                            "inputs": {
                                "user_input": {
                                    "type": "reference",
                                    "value": "input-1.output",
                                }
                            },
                        },
                        "output": "query",
                    }
                ],
                "edges": [
                    {
                        "source": "prompt-1",
                        "target": "prompt-2",
                        "condition": {"operator": "==", "value": "일번"},
                    }
                ],
                "graph_histories": [
                    {
                        "input_state": {"input-1_user_input": "일번"},
                        "output_state": {
                            "prompt-2_answer": "첫 번째 분기입니다."
                        },
                        "status": "success",
                    }
                ],
                "updated_by": "admin",
                "updated_at": datetime.now(),
            }
        }


class GraphDeleteRequest(BaseModel):
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class GraphDetail(GraphBase):
    id: UUID
    name: str
    description: Optional[str] = None
    version: Optional[int] = 1
    nodes: Optional[List[NodeDetail]] = None
    edges: Optional[List[EdgeDetail]] = None
    graph_histories: Optional[List[GraphHistoryDetail]] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    graph: GraphDetail


class GraphsResponse(BaseModel):
    graphs: List[GraphDetail]


class GraphIdResponse(BaseModel):
    id: UUID


class GraphIdsResponse(BaseModel):
    ids: List[UUID]


class NodeRunSchema(BaseModel):
    id: str
    type: str
    params: Dict[str, Any] = {}
    output: str = "output"  # state에 쓸 key


class EdgeRunSchema(BaseModel):
    source: str
    target: str


class GraphRunRequest(BaseModel):
    nodes: List[NodeRunSchema]
    edges: List[EdgeRunSchema]
    input_state: Dict[str, Any] = {}  # 사용자 입력
