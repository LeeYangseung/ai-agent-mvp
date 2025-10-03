from sqlalchemy import (
    CHAR,
    Column,
    ForeignKey,
    String,
    Integer,
    Text,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from app.database.models.base import Base, generate_uuid
import enum


class Chunk(Base):
    __table_args__ = {"comment": "청크 테이블"}

    id = Column(
        CHAR(36),
        default=generate_uuid,
        nullable=False,
        primary_key=True,
        index=True,
    )
    document_id = Column(
        CHAR(36),
        ForeignKey("document.id"),
        nullable=False,
        index=True,
        comment="문서 아이디",
    )
    chunk_index = Column(Integer, nullable=False, comment="청크 인덱스")
    content = Column(Text, nullable=False, comment="청크 내용")
    embedding_id = Column(String, nullable=True, comment="VectorDB key")
    chunk_size = Column(Integer, nullable=True, comment="실제 청크 크기")

    document = relationship("Document", back_populates="chunks")
