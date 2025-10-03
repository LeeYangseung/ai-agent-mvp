from sqlalchemy import (
    MetaData,
    Column,
    Boolean,
    DateTime,
    func,
    CHAR,
    String,
)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
import re
import uuid

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def generate_uuid():
    """Generate a UUID in binary format for MySQL."""
    return uuid.uuid4()


class CustomModelBase:

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:
        """
        클래스 이름을 기반으로 테이블 이름을 자동 생성
        CamelCase를 snake_case로 변환
        """
        name = re.sub(
            r"(?<!^)(?<![\W])(?=[A-Z][a-z])",
            "_",
            cls.__name__,
        ).lower()  # type: ignore
        return name

    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    is_deleted = Column(Boolean, default=False, comment="삭제여부")
    created_at = Column(
        DateTime, default=func.current_timestamp(), comment="생성일"
    )
    created_by = Column(String, comment="생성자")
    updated_at = Column(
        DateTime, default=func.current_timestamp(), comment="수정일"
    )
    updated_by = Column(String, comment="수정자")


metadata = MetaData(naming_convention=convention)
Base = declarative_base(cls=CustomModelBase, metadata=metadata)
