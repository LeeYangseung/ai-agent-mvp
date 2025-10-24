from abc import abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import Runnable
import logging

logger = logging.getLogger(__name__)


class BaseNode(Runnable):
    """모든 노드의 기본 클래스"""

    def __init__(
        self,
        output: str,
        llm: Optional[ChatOpenAI] = None,
        **kwargs,
    ):
        """
        Args:
            output: 출력을 저장할 state 키
            llm: LLM 인스턴스 (필요한 노드만 사용)
            **kwargs: 추가 파라미터
        """
        self.output = output
        self.llm = llm

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
                # "node-id.output" 형식 지원 (현재는 flat state이므로 output만 사용)
                if "." in var_value:
                    # node_id.output 형식
                    _, key = var_value.rsplit(".", 1)
                    actual_key = key
                else:
                    actual_key = var_value

                if actual_key and actual_key not in state:
                    logger.warning(
                        f"Variable '{var_name}' references '{actual_key}' "
                        f"which is not found in state. Available keys: "
                        f"{list(state.keys())}"
                    )

                input_vars[var_name] = state.get(actual_key, "")

        return input_vars

    @abstractmethod
    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        pass
