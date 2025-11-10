from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from uuid import uuid4
from app.schemas.enums import (
    DocumentStatus,
    ChunkingMethod,
    BreakpointThresholdType,
)
from app.schemas.rag.chunk import (
    ChunkDetail,
    ChunkCreateRequestAtDocument,
    ChunkUpdateRequest,
)
from app.schemas.rag.collection import CollectionDetail


class DocumentBase(BaseModel):
    collection_id: UUID
    name: str
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    method: Optional[ChunkingMethod] = ChunkingMethod.length
    breakpoint_threshold_type: Optional[BreakpointThresholdType] = (
        BreakpointThresholdType.percentile
    )
    status: Optional[DocumentStatus] = DocumentStatus.pending


class DocumentCreateRequest(DocumentBase):
    path: Optional[str] = None
    created_by: Optional[str] = "admin"
    updated_by: Optional[str] = created_by
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = created_at

    class Config:
        json_schema_extra = {
            "example": {
                "name": "document_name",
                "status": DocumentStatus.pending,
                "chunk_size": 500,
                "overlap_size": 100,
                "method": "length",
                "created_by": "admin",
                "created_at": datetime.now(),
                "updated_by": "admin",
                "updated_at": datetime.now(),
            }
        }


class DocumentUpdateRequest(DocumentBase):
    collection_id: Optional[UUID] = None
    name: Optional[str] = None
    path: Optional[str] = None
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    method: Optional[ChunkingMethod] = None
    breakpoint_threshold_type: Optional[BreakpointThresholdType] = None
    status: Optional[DocumentStatus] = None
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "document_name",
                "path": "document_path",
                "status": DocumentStatus.pending,
                "chunk_size": 500,
                "overlap_size": 100,
                "method": "length",
                "updated_by": "admin",
                "updated_at": datetime.now(),
            }
        }


class DocumentDeleteRequest(BaseModel):
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class DocumentDetail(BaseModel):
    id: UUID
    collection: Optional[CollectionDetail] = None
    name: str
    path: str
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    method: Optional[ChunkingMethod] = None
    breakpoint_threshold_type: Optional[BreakpointThresholdType] = None
    status: DocumentStatus
    chunks: Optional[List[ChunkDetail]] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None


class DocumentResponse(BaseModel):
    document: DocumentDetail


class DocumentsResponse(BaseModel):
    documents: List[DocumentDetail]


class DocumentIdResponse(BaseModel):
    id: UUID


class DocumentIdsResponse(BaseModel):
    ids: List[UUID]
