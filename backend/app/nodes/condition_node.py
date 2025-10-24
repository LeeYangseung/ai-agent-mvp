from typing import Dict, Any, List, Optional
from .base import BaseNode
import logging

logger = logging.getLogger(__name__)


class ConditionNode(BaseNode):
    """조건 분기 노드 - 입력값을 평가하여 다음 노드를 결정"""

    def __init__(
        self,
        output: str = "condition_result",
        inputs: Dict[str, Dict[str, str]] = None,
        conditions: List[Dict[str, str]] = None,
        default_target: str = "",
        **kwargs,
    ):
        """
        Args:
            output: 출력 키 (조건 평가 결과 저장)
            inputs: 입력 변수들
                   예: {"answer": {"type": "reference", "value": "answer"}}
            conditions: 조건 리스트
                   예: [
                       {
                           "variable": "answer",
                           "operator": "contains",
                           "value": "긍정적",
                           "target": "node-id-1"
                       }
                   ]
            default_target: 모든 조건 불만족 시 이동할 노드 ID (ELSE)
        """
        super().__init__(output=output, **kwargs)
        self.inputs = inputs or {}
        self.conditions = conditions or []
        self.default_target = default_target

    def _evaluate_condition(
        self, variable_value: Any, operator: str, compare_value: str
    ) -> bool:
        """
        단일 조건을 평가

        Args:
            variable_value: 평가할 변수 값
            operator: 비교 연산자
            compare_value: 비교 대상 값

        Returns:
            조건 만족 여부
        """
        # 문자열로 변환 (비교를 위해)
        var_str = str(variable_value)
        comp_str = str(compare_value)

        try:
            if operator == "==":
                return var_str == comp_str
            elif operator == "!=":
                return var_str != comp_str
            elif operator == "<>":
                return var_str != comp_str
            elif operator == "contains":
                return comp_str in var_str
            elif operator == "not_contains":
                return comp_str not in var_str
            elif operator == "starts_with":
                return var_str.startswith(comp_str)
            elif operator == "ends_with":
                return var_str.endswith(comp_str)
            elif operator == ">":
                # 숫자 비교 시도
                try:
                    return float(var_str) > float(comp_str)
                except ValueError:
                    return var_str > comp_str
            elif operator == ">=":
                try:
                    return float(var_str) >= float(comp_str)
                except ValueError:
                    return var_str >= comp_str
            elif operator == "<":
                try:
                    return float(var_str) < float(comp_str)
                except ValueError:
                    return var_str < comp_str
            elif operator == "<=":
                try:
                    return float(var_str) <= float(comp_str)
                except ValueError:
                    return var_str <= comp_str
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.error(
                f"Condition evaluation error: {e} "
                f"(variable={var_str}, operator={operator}, "
                f"compare={comp_str})"
            )
            return False

    def invoke(self, state: Dict[str, Any], config=None) -> Dict[str, Any]:
        """
        조건을 평가하고 다음 노드를 결정

        Returns:
            state에 다음 노드 정보 추가
        """
        # 1. BaseNode의 공통 메서드로 inputs 처리
        input_vars = self._resolve_inputs(self.inputs, state)

        # 2. 각 조건을 순서대로 평가
        next_node = None
        matched_condition = None

        for i, condition in enumerate(self.conditions):
            variable_name = condition.get("variable", "")
            operator = condition.get("operator", "==")
            compare_value = condition.get("value", "")
            target = condition.get("target", "")

            # input_vars에서 변수 값 가져오기
            if variable_name not in input_vars:
                logger.warning(
                    f"ConditionNode({self.output}): "
                    f"Variable '{variable_name}' not found in inputs. "
                    f"Available: {list(input_vars.keys())}"
                )
                continue

            variable_value = input_vars[variable_name]

            # 조건 평가
            is_satisfied = self._evaluate_condition(
                variable_value, operator, compare_value
            )

            logger.debug(
                f"ConditionNode({self.output}): "
                f"Condition {i+1}: '{variable_name}' ({variable_value}) "
                f"{operator} '{compare_value}' = {is_satisfied}"
            )

            if is_satisfied:
                next_node = target
                matched_condition = i
                logger.info(
                    f"ConditionNode({self.output}): "
                    f"Condition {i+1} matched, routing to '{target}'"
                )
                break

        # 3. 조건 불만족 시 default_target 사용
        if next_node is None:
            next_node = self.default_target
            logger.info(
                f"ConditionNode({self.output}): "
                f"No condition matched, routing to default '{next_node}'"
            )

        # 4. 결과를 state에 저장
        new_state = dict(state)
        new_state[self.output] = {
            "next_node": next_node,
            "matched_condition": matched_condition,
            "input_vars": input_vars,
        }

        # 5. 라우팅 정보를 특별한 키에 저장 (graph_runner가 사용)
        new_state["__next__"] = next_node

        return new_state

    def get_next_node(self, state: Dict[str, Any]) -> str:
        """
        LangGraph의 조건부 엣지에서 사용할 함수

        Args:
            state: 현재 그래프 상태

        Returns:
            다음 노드 ID
        """
        return state.get("__next__", self.default_target)
