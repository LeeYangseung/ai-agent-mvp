# app/schemas/graph/edge.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class EdgeBase(BaseModel):
    source: str
    target: str
    condition: Optional[Dict[str, Any]] = None


class EdgeCreateRequest(EdgeBase):
    graph_id: Optional[UUID] = None
    created_by: Optional[str] = "admin"
    updated_by: Optional[str] = created_by
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = created_at

    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "599ee5ea-4ce9-4b52-9f69-b8bfe057bb08",
                "source": "prompt-1",
                "target": "retrieval-1",
                "condition": {"operator": "==", "value": "일번"},
            }
        }


class EdgeUpdateRequest(EdgeBase):
    source: Optional[str] = None
    target: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class EdgeDeleteRequest(BaseModel):
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class EdgeDetail(EdgeBase):
    id: UUID
    graph_id: UUID
    source: str
    target: str
    condition: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EdgeResponse(BaseModel):
    edge: EdgeDetail


class EdgesResponse(BaseModel):
    edges: List[EdgeDetail]


class EdgeIdResponse(BaseModel):
    id: UUID


class EdgeIdsResponse(BaseModel):
    ids: List[UUID]
