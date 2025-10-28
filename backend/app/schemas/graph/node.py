# app/schemas/graph/node.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class NodeBase(BaseModel):
    node_id: str
    type: str
    params: Optional[Dict[str, Any]] = None
    output: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    order: Optional[int] = None


class NodeCreateRequest(NodeBase):
    graph_id: Optional[UUID] = None
    created_by: Optional[str] = "admin"
    updated_by: Optional[str] = created_by
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = created_at

    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "599ee5ea-4ce9-4b52-9f69-b8bfe057bb08",
                "node_id": "prompt-1",
                "type": "PromptNode",
                "params": {
                    "system_prompt": "당신은 친절한 AI입니다.",
                    "user_prompt": "질문: {user_input}",
                    "inputs": {
                        "user_input": {
                            "type": "reference",
                            "value": "input-1.user_input",
                        }
                    },
                },
                "output": "answer",
                "position": {"x": 100, "y": 200},
                "order": 1,
            }
        }


class NodeUpdateRequest(NodeBase):
    node_id: Optional[str] = None
    type: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    output: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    order: Optional[int] = None
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class NodeDeleteRequest(BaseModel):
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class NodeDetail(NodeBase):
    id: UUID
    graph_id: UUID
    node_id: str
    type: str
    params: Optional[Dict[str, Any]] = None
    output: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    order: Optional[int] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NodeResponse(BaseModel):
    node: NodeDetail


class NodesResponse(BaseModel):
    nodes: List[NodeDetail]


class NodeIdResponse(BaseModel):
    id: UUID


class NodeIdsResponse(BaseModel):
    ids: List[UUID]
