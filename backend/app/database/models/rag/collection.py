from sqlalchemy import (
    CHAR,
    Column,
    String,
)
from sqlalchemy.orm import relationship

from app.database.models.base import Base, generate_uuid


class Collection(Base):
    __table_args__ = {"comment": "컬렉션 테이블"}

    id = Column(
        CHAR(36),
        default=generate_uuid,
        nullable=False,
        primary_key=True,
        index=True,
    )
    name = Column(
        String(255), nullable=False, comment="컬렉션 이름"
    )
    description = Column(String(500), nullable=True, comment="컬렉션 설명")

    documents = relationship(
        "Document", back_populates="collection", cascade="all, delete-orphan"
    )
