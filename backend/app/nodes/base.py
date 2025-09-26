from abc import abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import Runnable


class BaseNode(Runnable):
    def __init__(
        self,
        input_key: str,
        output_key: str,
        template: str = "",
        variables: Dict[str, Any] = None,
        llm: Optional[ChatOpenAI] = None,
    ):
        self.input_key = input_key
        self.output_key = output_key
        self.template = template
        self.variables = variables or {}
        self.llm = llm  # 외부에서 주입

    @abstractmethod
    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        pass
