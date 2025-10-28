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


class Node(Base):
    __table_args__ = {"comment": "그래프 테이블"}

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
    node_id = Column(
        String, nullable=False, comment="UI에서 사용하는 노드 아이디"
    )
    type = Column(String(100), nullable=False)
    params = Column(JSON, nullable=True)
    output = Column(String(100), nullable=True)
    position = Column(JSON, nullable=True)
    order = Column(Integer, nullable=True)

    graph = relationship("Graph", back_populates="nodes")
