from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from .base import BaseNode
from langchain.schema.messages import SystemMessage, HumanMessage, AIMessage
import logging

logger = logging.getLogger(__name__)


class PromptNode(BaseNode):
    """프롬프트 실행 노드"""

    def __init__(
        self,
        output: str,
        system_prompt: str = "",
        user_prompt: str = "",
        assistant_prompt: str = "",
        inputs: Dict[str, Dict[str, str]] = None,
        llm: Optional[ChatOpenAI] = None,
        **kwargs,
    ):
        """
        Args:
            output: 출력을 저장할 키
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            assistant_prompt: 어시스턴트 프롬프트
                            (선택적, few-shot learning용)
            inputs: 입력 변수들
                   예: {"user_input":
                        {"type": "reference", "value": "user_input"},
                        "language":
                        {"type": "fixed", "value": "한국어"}}
            llm: LLM 인스턴스
        """
        super().__init__(output=output, llm=llm, **kwargs)
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.assistant_prompt = assistant_prompt
        self.inputs = inputs or {}

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        if self.llm is None:
            raise ValueError("LLM instance is required but not provided.")

        # 1. BaseNode의 공통 메서드로 inputs 처리
        input_vars = self._resolve_inputs(self.inputs, state)

        # 2. 메시지 구성
        messages = []

        if self.system_prompt:
            try:
                formatted_system = self.system_prompt.format(**input_vars)
                messages.append(SystemMessage(content=formatted_system))
            except KeyError as e:
                logger.error(
                    f"PromptNode({self.output}): "
                    f"system_prompt formatting error: {e}"
                )
                raise ValueError(
                    f"Missing variable {e} in system_prompt. "
                    f"Available: {list(input_vars.keys())}"
                )

        if self.user_prompt:
            try:
                formatted_user = self.user_prompt.format(**input_vars)
                messages.append(HumanMessage(content=formatted_user))
            except KeyError as e:
                logger.error(
                    f"PromptNode({self.output}): "
                    f"user_prompt formatting error: {e}"
                )
                raise ValueError(
                    f"Missing variable {e} in user_prompt. "
                    f"Available: {list(input_vars.keys())}"
                )

        if self.assistant_prompt:
            try:
                formatted_assistant = self.assistant_prompt.format(
                    **input_vars
                )
                messages.append(AIMessage(content=formatted_assistant))
                # Few-shot 예시 후 실제 사용자 질문 추가
                # (대화 흐름: System → User → Assistant(예시) → User(실제))
                if self.user_prompt:
                    messages.append(HumanMessage(content=formatted_user))
            except KeyError as e:
                logger.error(
                    f"PromptNode({self.output}): "
                    f"assistant_prompt formatting error: {e}"
                )
                raise ValueError(
                    f"Missing variable {e} in assistant_prompt. "
                    f"Available: {list(input_vars.keys())}"
                )

        if not messages:
            raise ValueError(
                "PromptNode requires at least one prompt "
                "(system_prompt, user_prompt, or assistant_prompt)"
            )

        # 3. LLM 호출
        try:
            result = self.llm.invoke(messages)
        except Exception as e:
            logger.error(
                f"PromptNode({self.output}): LLM invocation failed: {e}"
            )
            raise

        # 4. output에 저장
        new_state = dict(state)
        new_state[self._get_state_key()] = result.content
        return new_state
