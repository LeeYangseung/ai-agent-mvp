from abc import abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
import logging

logger = logging.getLogger(__name__)


class BaseNode(Runnable):
    """모든 노드의 기본 클래스"""

    def __init__(
        self,
        output: str,
        llm: Optional[ChatOpenAI] = None,
        node_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Args:
            output: 출력을 저장할 state 키
            llm: LLM 인스턴스 (필요한 노드만 사용)
            node_id: 노드 ID (state 키 생성용)
            **kwargs: 추가 파라미터
        """
        self.output = output
        self.node_id = node_id
        self.llm = llm

    def _get_state_key(self) -> str:
        """state에 저장할 키를 생성합니다. {node_id}_{output_key} 형태"""
        if self.node_id:
            return f"{self.node_id}_{self.output}"
        return self.output

    def _resolve_inputs(
        self, inputs: Dict[str, Dict[str, str]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        inputs 구조를 실제 값으로 변환하는 공통 메서드

        Args:
            inputs: {"변수명": {"type": "reference/fixed", "value": "값"}}
            state: 현재 그래프 상태

        Returns:
            변환된 변수 딕셔너리
        """
        input_vars = {}

        for var_name, var_config in inputs.items():
            var_type = var_config.get("type", "reference")
            var_value = var_config.get("value", "")

            if var_type == "fixed":
                # 고정값 사용
                input_vars[var_name] = var_value
            elif var_type == "reference":
                # state에서 참조
                # "node_id_output_key" 형식 지원 (새로운 키 형식)
                actual_key = var_value

                if actual_key and actual_key not in state:
                    logger.warning(
                        f"Variable '{var_name}' references '{actual_key}' "
                        f"which is not found in state. Available keys: "
                        f"{list(state.keys())}"
                    )

                input_vars[var_name] = state.get(actual_key, "")

        return input_vars

    def _handle_error(
        self, error: Exception, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        에러를 처리하고 [ERROR] 형식으로 output에 저장하는 공통 메서드

        Args:
            error: 발생한 예외
            state: 현재 그래프 상태

        Returns:
            에러 메시지가 포함된 새로운 state
        """
        error_message = f"[ERROR] {str(error)}"
        logger.error(
            f"{self.__class__.__name__}({self.output}): {error_message}"
        )

        new_state = dict(state)
        new_state[self._get_state_key()] = error_message
        new_state["graph_status"] = "failed"
        return new_state

    @abstractmethod
    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        pass
