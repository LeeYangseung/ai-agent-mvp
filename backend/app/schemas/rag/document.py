from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from uuid import uuid4
from app.schemas.enums import DocumentStatus
from app.schemas.rag.chunk import (
    ChunkDetail,
    ChunkCreateRequestAtDocument,
    ChunkUpdateRequest,
)


class DocumentBase(BaseModel):
    name: str
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    method: Optional[str] = None
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
                "method": "overlap",
                "created_by": "admin",
                "created_at": datetime.now(),
                "updated_by": "admin",
                "updated_at": datetime.now(),
            }
        }


class DocumentUpdateRequest(DocumentBase):
    name: Optional[str] = None
    path: Optional[str] = None
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    method: Optional[str] = None
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
                "method": "overlap",
                "updated_by": "admin",
                "updated_at": datetime.now(),
            }
        }


class DocumentDeleteRequest(BaseModel):
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class DocumentDetail(BaseModel):
    id: UUID
    name: str
    path: str
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    method: Optional[str] = None
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
