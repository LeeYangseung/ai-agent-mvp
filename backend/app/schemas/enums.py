from enum import Enum


class DocumentStatus(str, Enum):
    pending = "pending"
    indexed = "indexed"
    deleted = "deleted"


class ChunkingMethod(str, Enum):
    length = "length"
    semantic = "semantic"
    hybrid = "hybrid"
    paragraph = "paragraph"


class BreakpointThresholdType(str, Enum):
    percentile = "percentile"
    standard_deviation = "standard_deviation"
    interquartile = "interquartile"
