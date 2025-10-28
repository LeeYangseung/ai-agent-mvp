from sqlalchemy import (
    CHAR,
    Column,
    String,
    Integer,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database.models.base import Base, generate_uuid


class Edge(Base):
    __table_args__ = {"comment": "엣지 테이블"}

    id = Column(
        CHAR(36),
        default=generate_uuid,
        nullable=False,
        primary_key=True,
        index=True,
    )
    graph_id = Column(
        CHAR(36),
        ForeignKey("graph.id"),
        nullable=False,
        index=True,
        comment="그래프 아이디",
    )
    source = Column(String(100), nullable=False)
    target = Column(String(100), nullable=False)
    condition = Column(JSON, nullable=True)

    graph = relationship("Graph", back_populates="edges")
