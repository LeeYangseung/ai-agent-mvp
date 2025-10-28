from typing import Dict, Any, Optional
from .base import BaseNode
import logging

logger = logging.getLogger(__name__)


class OutputNode(BaseNode):
    """그래프의 출구점 노드 - state를 최종 출력으로 포맷팅"""

    def __init__(
        self,
        output: str = "agent_output",
        wrap_template: Optional[str] = None,
        inputs: Dict[str, Dict[str, str]] = None,
        **kwargs,
    ):
        """
        Args:
            output: 출력을 저장할 키 (기본값: agent_output)
            wrap_template: 출력 포맷 템플릿
            inputs: 템플릿에 사용할 변수들
                   예: {"answer": {"type": "reference",
                                   "value": "answer"},
                        "user_input": {"type": "reference",
                                       "value": "user_input"}}
        """
        super().__init__(output=output, **kwargs)
        self.wrap_template = wrap_template or ""
        self.inputs = inputs or {}

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """
        state에서 최종 결과를 추출하고 포맷팅

        Args:
            state: 현재 그래프 상태
            config: 설정 (사용하지 않음)

        Returns:
            포맷팅된 최종 출력이 포함된 state
        """
        try:
            # 0. 그래프 상태 확인
            if state.get("graph_status") == "failed":
                return state
            # 1. 기존 state 복사
            new_state = dict(state)

            # 2. BaseNode의 공통 메서드로 inputs 처리
            input_vars = self._resolve_inputs(self.inputs, state)

            # 3. wrap_template이 있으면 포맷팅 적용
            if self.wrap_template:
                try:
                    formatted_output = self.wrap_template.format(**input_vars)
                    logger.debug(
                        f"OutputNode({self.output}): "
                        f"Formatted output with template"
                    )
                except KeyError as e:
                    raise ValueError(
                        f"Template formatting error: {str(e)}. "
                        f"Template: {self.wrap_template}, "
                        f"Available variables: {list(input_vars.keys())}"
                    )
            else:
                # wrap_template이 없으면 첫 번째 input 값만 사용
                if input_vars:
                    # 첫 번째 input을 출력으로 사용
                    first_key = next(iter(input_vars))
                    formatted_output = str(input_vars[first_key])
                    logger.debug(
                        f"OutputNode({self.output}): "
                        f"No template, using first input '{first_key}'"
                    )
                else:
                    formatted_output = ""
                    logger.warning(
                        f"OutputNode({self.output}): "
                        f"No template and no inputs provided"
                    )

            # 4. output에 최종 출력 저장
            new_state[self._get_state_key()] = formatted_output

            logger.info(
                f"OutputNode({self.output}): "
                f"Generated output ({len(formatted_output)} chars)"
            )

            return new_state

        except Exception as e:
            return self._handle_error(e, state)

    def set_wrap_template(self, template: str):
        """런타임에 포맷팅 템플릿 설정"""
        self.wrap_template = template
