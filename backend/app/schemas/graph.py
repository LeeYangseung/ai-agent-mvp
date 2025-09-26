from pydantic import BaseModel
from typing import Dict, Any, List


class NodeSchema(BaseModel):
    id: str
    type: str
    params: Dict[str, Any] = {}
    input_key: str = "input"  # state에서 읽을 key
    output_key: str = "output"  # state에 쓸 key


class EdgeSchema(BaseModel):
    source: str
    target: str


class GraphRequest(BaseModel):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
    input_state: Dict[str, Any] = {}  # 사용자 입력
