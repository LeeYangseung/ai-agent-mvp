from typing import Dict, Any, Optional
from .base import BaseNode


class OutputNode(BaseNode):
    """그래프의 출구점 노드 - state를 최종 출력으로 포맷팅"""

    def __init__(
        self,
        input_key: str,
        wrap_template: Optional[str] = None,
        output_key: str = "final_output",
        **kwargs,
    ):
        super().__init__(input_key=input_key, output_key=output_key, **kwargs)
        self.wrap_template = wrap_template

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """
        state에서 최종 결과를 추출하고 포맷팅

        Args:
            state: 현재 그래프 상태
            config: 설정 (사용하지 않음)

        Returns:
            포맷팅된 최종 출력이 포함된 state
        """
        # 1. 기존 state 복사
        new_state = dict(state)

        # 2. input_key에서 최종 결과 추출
        final_result = state.get(self.input_key, "")

        # 3. wrap_template이 있으면 포맷팅 적용
        if self.wrap_template:
            try:
                # template의 {변수명} 부분을 state의 값으로 치환
                formatted_output = self.wrap_template.format(**state)
                # input_key의 값도 별도로 치환
                formatted_output = formatted_output.replace(
                    f"{{{self.input_key}}}", str(final_result)
                )
            except KeyError:
                # template에 없는 변수가 있으면 기본값으로 처리
                formatted_output = self.wrap_template.replace(
                    f"{{{self.input_key}}}", str(final_result)
                )
        else:
            # wrap_template이 없으면 그대로 사용
            formatted_output = final_result

        # 4. output_key에 최종 출력 저장
        new_state[self.output_key] = formatted_output

        return new_state

    def set_wrap_template(self, template: str):
        """런타임에 포맷팅 템플릿 설정"""
        self.wrap_template = template
