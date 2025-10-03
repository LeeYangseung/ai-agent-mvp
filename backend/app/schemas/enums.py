from enum import Enum


class DocumentStatus(str, Enum):
    pending = "pending"
    indexed = "indexed"
    deleted = "deleted"
