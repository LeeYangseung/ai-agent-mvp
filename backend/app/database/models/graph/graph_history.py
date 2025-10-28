from sqlalchemy import (
    CHAR,
    Column,
    String,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.models.base import Base, generate_uuid


class GraphHistory(Base):
    __table_args__ = {"comment": "그래프 히스토리 테이블"}

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
    input_state = Column(JSON, nullable=False, comment="입력 상태")
    output_state = Column(JSON, nullable=True, comment="출력 상태")
    status = Column(String(50), default="success", comment="상태")
    error_message = Column(Text, nullable=True, comment="에러 메시지")

    graph = relationship("Graph", back_populates="graph_histories")
