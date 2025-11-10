from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class CollectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class CollectionCreateRequest(CollectionBase):
    created_by: Optional[str] = "admin"
    updated_by: Optional[str] = "admin"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "my_collection",
                "description": "컬렉션 설명",
                "created_by": "admin",
            }
        }


class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "updated_collection",
                "description": "수정된 설명",
                "updated_by": "admin",
            }
        }


class CollectionDeleteRequest(BaseModel):
    updated_by: Optional[str] = "admin"
    updated_at: Optional[datetime] = None


class CollectionDetail(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    document_count: Optional[int] = 0
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None


class CollectionResponse(BaseModel):
    collection: CollectionDetail


class CollectionsResponse(BaseModel):
    collections: List[CollectionDetail]


class CollectionIdResponse(BaseModel):
    id: UUID


class CollectionIdsResponse(BaseModel):
    ids: List[UUID]
