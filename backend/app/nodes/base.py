from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI


class BaseNode(ABC):
    """모든 노드의 공통 추상 클래스"""

    def __init__(
        self,
        node_id: str,
        params: Dict[str, Any],
        llm: Optional[ChatOpenAI] = None,
    ):
        self.node_id = node_id
        self.params = params
        self.llm = llm

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """노드 실행"""
        pass
