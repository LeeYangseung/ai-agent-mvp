from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from uuid import uuid4


class ChunkBase(BaseModel):
    document_id: Optional[UUID] = None
    chunk_index: int
    content: str
    embedding_id: str
    chunk_size: int


class ChunkCreateRequest(ChunkBase):
    document_id: UUID
    created_by: Optional[str] = "admin"
    updated_by: Optional[str] = created_by
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = created_at

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": str(uuid4()),
                "chunk_index": 1,
                "content": "content",
                "embedding_id": "embedding_id",
                "chunk_size": 500,
                "created_by": "admin",
                "created_at": datetime.now(),
                "updated_by": "admin",
                "updated_at": datetime.now(),
            }
        }


class ChunkCreateRequestAtDocument(ChunkCreateRequest):
    document_id: Optional[UUID] = None


class ChunkUpdateRequest(ChunkBase):
    chunk_index: Optional[int]
    content: Optional[str]
    embedding_id: Optional[str]
    chunk_size: Optional[int]
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_index": 1,
                "content": "content",
                "embedding_id": "embedding_id",
                "chunk_size": 500,
                "updated_by": "admin",
                "updated_at": datetime.now(),
            }
        }


class ChunkDeleteRequest(BaseModel):
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = datetime.now()


class ChunkDetail(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    embedding_id: str
    chunk_size: int
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None


class ChunkResponse(BaseModel):
    chunk: ChunkDetail


class ChunksResponse(BaseModel):
    chunks: List[ChunkDetail]


class ChunkIdResponse(BaseModel):
    id: UUID


class ChunkIdsResponse(BaseModel):
    ids: List[UUID]
