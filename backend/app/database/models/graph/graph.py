from sqlalchemy import (
    CHAR,
    Column,
    String,
    Integer,
)
from sqlalchemy.orm import relationship

from app.database.models.base import Base, generate_uuid


class Graph(Base):
    __table_args__ = {"comment": "그래프 테이블"}

    id = Column(
        CHAR(36),
        default=generate_uuid,
        nullable=False,
        primary_key=True,
        index=True,
    )
    name = Column(String, nullable=False, comment="그래프 이름")
    description = Column(String, nullable=False, comment="그래프 설명")
    version = Column(Integer, nullable=False, comment="그래프 버전")

    nodes = relationship(
        "Node", back_populates="graph", cascade="all, delete-orphan"
    )
    edges = relationship(
        "Edge", back_populates="graph", cascade="all, delete-orphan"
    )
    graph_histories = relationship(
        "GraphHistory",
        back_populates="graph",
        cascade="all, delete-orphan",
    )
