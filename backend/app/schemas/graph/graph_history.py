# app/schemas/graph/history.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class GraphHistoryBase(BaseModel):
    input_state: Dict[str, Any]
    output_state: Optional[Dict[str, Any]] = None
    status: Optional[str] = "success"
    error_message: Optional[str] = None


class GraphHistoryCreateRequest(GraphHistoryBase):
    graph_id: Optional[UUID] = None
    created_by: Optional[str] = "admin"
    updated_by: Optional[str] = created_by
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = created_at

    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "599ee5ea-4ce9-4b52-9f69-b8bfe057bb08",
                "input_state": {"input-1_user_input": "일번"},
                "output_state": {"prompt-2_answer": "첫 번째 분기입니다."},
                "status": "success",
            }
        }


class GraphHistoryUpdateRequest(GraphHistoryBase):
    input_state: Optional[Dict[str, Any]] = None
    output_state: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class GraphHistoryDetail(GraphHistoryBase):
    id: UUID
    graph_id: UUID
    input_state: Dict[str, Any]
    output_state: Optional[Dict[str, Any]] = None
    status: Optional[str] = "success"
    error_message: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GraphHistoryDeleteRequest(BaseModel):
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class GraphHistoryResponse(BaseModel):
    graph_history: GraphHistoryDetail


class GraphHistoriesResponse(BaseModel):
    graph_histories: List[GraphHistoryDetail]


class GraphHistoryIdResponse(BaseModel):
    id: UUID


class GraphHistoryIdsResponse(BaseModel):
    ids: List[UUID]
