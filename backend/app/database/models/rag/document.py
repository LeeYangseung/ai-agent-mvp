from sqlalchemy import (
    CHAR,
    Column,
    String,
    Enum,
    Integer,
)
from sqlalchemy.orm import relationship

from app.database.models.base import Base, generate_uuid
from app.schemas.enums import (
    DocumentStatus,
    ChunkingMethod,
    BreakpointThresholdType,
)


class Document(Base):
    __table_args__ = {"comment": "문서 테이블"}

    id = Column(
        CHAR(36),
        default=generate_uuid,
        nullable=False,
        primary_key=True,
        index=True,
    )
    name = Column(String, nullable=False, comment="문서 이름")
    path = Column(String, nullable=False, comment="문서 경로")
    chunk_size = Column(
        Integer, nullable=True, comment="청킹 전략 - 청크 크기"
    )
    overlap_size = Column(
        Integer, nullable=True, comment="청킹 전략 - 청크 중복 크기"
    )
    method = Column(
        Enum(ChunkingMethod),
        default=ChunkingMethod.length,
        nullable=True,
        comment="청킹 전략 - 청크 방법",
    )
    breakpoint_threshold_type = Column(
        Enum(BreakpointThresholdType),
        default=BreakpointThresholdType.percentile,
        nullable=True,
        comment="시맨틱 청킹 전략 - 임계값 유형",
    )
    status = Column(
        Enum(DocumentStatus),
        default=DocumentStatus.pending,
        comment="문서 상태",
    )

    chunks = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )
