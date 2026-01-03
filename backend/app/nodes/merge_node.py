from typing import Dict, Any, List, Optional
from .base import BaseNode
import logging

logger = logging.getLogger(__name__)


class MergeNode(BaseNode):
    """
    Fan-in 노드 - 여러 병렬 브랜치의 결과를 하나로 병합
    
    병렬 실행된 여러 노드의 출력을 수집하여 하나의 결과로 합칩니다.
    """

    def __init__(
        self,
        output: str = "merged_output",
        inputs: Dict[str, Dict[str, str]] = None,
        merge_strategy: str = "concat",
        separator: str = "\n\n---\n\n",
        **kwargs,
    ):
        """
        Args:
            output: 병합된 결과를 저장할 키
            inputs: 병합할 입력 변수들
                   예: {
                       "result1": {"type": "reference", "value": "node-3_agent_output"},
                       "result2": {"type": "reference", "value": "node-4_agent_output"}
                   }
            merge_strategy: 병합 전략
                - "concat": 문자열 연결 (기본값)
                - "list": 리스트로 수집
                - "dict": 딕셔너리로 수집
            separator: concat 모드에서 사용할 구분자
        """
        super().__init__(output=output, **kwargs)
        self.inputs = inputs or {}
        self.merge_strategy = merge_strategy
        self.separator = separator

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """
        여러 브랜치의 결과를 병합

        Args:
            state: 현재 그래프 상태

        Returns:
            병합된 결과를 포함한 업데이트된 state
        """
        try:
            # 0. 그래프 상태 확인
            if state.get("graph_status") == "failed":
                return state

            # 1. BaseNode의 공통 메서드로 inputs 처리
            input_vars = self._resolve_inputs(self.inputs, state)

            logger.debug(
                f"MergeNode({self.output}): "
                f"Merging {len(input_vars)} inputs with "
                f"strategy '{self.merge_strategy}'"
            )

            # 2. 병합 전략에 따라 결과 생성
            if self.merge_strategy == "concat":
                # 문자열 연결
                merged_result = self.separator.join(
                    str(v) for v in input_vars.values() if v
                )

            elif self.merge_strategy == "list":
                # 리스트로 수집
                merged_result = list(input_vars.values())

            elif self.merge_strategy == "dict":
                # 딕셔너리로 수집 (키 이름 유지)
                merged_result = input_vars

            else:
                # 기본값: concat
                merged_result = self.separator.join(
                    str(v) for v in input_vars.values() if v
                )

            # 3. 결과를 state에 저장
            new_state = dict(state)
            new_state[self._get_state_key()] = merged_result

            logger.info(
                f"MergeNode({self.output}): "
                f"Merged {len(input_vars)} inputs "
                f"(result length: {len(str(merged_result))})"
            )

            return new_state

        except Exception as e:
            return self._handle_error(e, state)

