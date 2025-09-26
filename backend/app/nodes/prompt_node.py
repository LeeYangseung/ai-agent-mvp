from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from .base import BaseNode
from langchain.prompts import ChatPromptTemplate


class PromptNode(BaseNode):
    """프롬프트 실행 노드"""

    def __init__(
        self,
        input_key: str,
        output_key: str,
        template: str = "",
        variables: Dict[str, Any] = None,
        llm: Optional[ChatOpenAI] = None,
    ):
        super().__init__(input_key, output_key, template, variables, llm)

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        if self.llm is None:
            raise ValueError("LLM instance is required but not provided.")

        # 1. input_key를 기준으로 state에서 꺼냄
        input_val = state.get(self.input_key, "")
        input_vars = {**self.variables, self.input_key: input_val}

        # 2. 프롬프트 생성 및 실행
        prompt = ChatPromptTemplate.from_template(self.template)
        chain = prompt | self.llm
        result = chain.invoke(input_vars)

        # 3. output_key에 저장
        new_state = dict(state)
        new_state[self.output_key] = result.content
        return new_state
