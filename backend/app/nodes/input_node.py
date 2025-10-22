from typing import Dict, Any, Optional
from .base import BaseNode


class InputNode(BaseNode):
    """그래프의 진입점 노드 - 외부 입력을 state로 변환"""

    def __init__(
        self,
        output: str = "user_input",
        input_data: Optional[Any] = None,
        **kwargs,
    ):
        """
        Args:
            output: 출력 키 (기본값: user_input, 프론트엔드와 일관성 유지)
            input_data: 런타임에 주입할 입력 데이터 (선택적)
        """
        super().__init__(output=output, **kwargs)
        self.input_data = input_data

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """
        외부에서 받은 입력을 state에 추가

        Args:
            state: 현재 그래프 상태
            config: 설정 (사용하지 않음)

        Returns:
            업데이트된 state
        """
        # 1. 기존 state 복사
        new_state = dict(state)

        # 2. input_data가 있으면 사용, 없으면 state에서 "input" 키로 찾기
        if self.input_data is not None:
            input_value = self.input_data
        else:
            # 외부에서 전달된 입력 데이터를 state에서 찾기
            # 일반적으로 "input" 키로 전달됨
            input_value = state.get("input", "")

        # 3. output에 입력 데이터 저장 (기본: user_input)
        new_state[self.output] = input_value

        return new_state

    def set_input_data(self, data: Any):
        """런타임에 입력 데이터 설정"""
        self.input_data = data
