from typing import Dict, Any, List, Union, Annotated, TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from app.nodes.prompt_node import PromptNode
from app.nodes.retrieval_node import RetrievalNode
from app.nodes.input_node import InputNode
from app.nodes.output_node import OutputNode
from app.nodes.condition_node import ConditionNode
from app.nodes.merge_node import MergeNode
import logging
import operator

logger = logging.getLogger(__name__)


def add_dicts(left: dict, right: dict) -> dict:
    """
    두 dict를 병합하는 reducer 함수
    병렬 실행 시 각 브랜치의 state 업데이트를 병합합니다.
    나중 값이 이전 값을 덮어씁니다.
    """
    if left is None:
        return right or {}
    if right is None:
        return left or {}

    result = dict(left)
    result.update(right)
    return result


# 병렬 업데이트를 지원하는 State Schema
# Annotated[dict, add_dicts]를 사용하여 병합 로직 지정
OverallState = Annotated[dict, add_dicts]


async def run_graph(graph_json: Dict[str, Any], llm):
    """
    그래프를 실행하는 메인 함수

    graph_json 구조 (최신 버전):
    {
      "nodes": [
        {
          "id": "input-1",
          "type": "InputNode",
          "params": {},
          "output": "user_input"  # 기본값: "user_input"
        },
        {
          "id": "retrieval-1",
          "type": "RetrievalNode",
          "params": {
            "top_k": 4,
            "collection": "",
            "inputs": {
              "query": {"type": "reference", "value": "user_input"}
            }
          },
          "output": "context"
        },
        {
          "id": "condition-1",
          "type": "ConditionNode",
          "params": {
            "evaluation_mode": "first_match",  # or "all_matches" (fan-out)
            "inputs": {
              "answer": {"type": "reference", "value": "answer"}
            },
            "conditions": [
              {
                "variable": "answer",
                "operator": "contains",
                "value": "긍정적",
                "target": "node-positive"
              }
            ],
            "default_target": "node-default"
          },
          "output": "condition_result"
        }
      ],
      "edges": [...],
      "input_state": {
        "input": "서울 날씨 어때?"
      }
    }

    상태 관리 (State Management):
    - Dict[str, Any] 기반 유연한 상태 관리
    - __next__: 다음 노드 결정용 특수 키
      * first_match: str (단일 노드 ID)
      * all_matches: List[str] (병렬 실행할 노드 ID 리스트)
    - 각 노드의 출력: {node_id}_{output_key} 형태로 저장
    """
    nodes = graph_json.get("nodes", [])
    edges = graph_json.get("edges", [])
    input_state = graph_json.get("input_state", {})

    # 스키마에서 이미 output 필드만 사용하도록 수정됨

    logger.info(f"Starting graph execution with {len(nodes)} nodes")

    # Annotated reducer를 사용하여 병렬 업데이트 지원
    # 각 병렬 브랜치가 state를 업데이트할 때 add_dicts로 병합됨
    workflow = StateGraph(OverallState)
    node_map = {}

    # 1. 노드 생성
    condition_nodes = []  # ConditionNode 목록 (나중에 조건부 엣지 추가)
    for node in nodes:
        node_id = node["id"]
        node_type = node["type"]
        params = node.get("params", {})
        output = node.get("output")

        logger.debug(f"Creating node: {node_id} (type: {node_type})")

        try:
            node_impl = _create_node(
                node_type, node_id, params, output, node, llm
            )
            workflow.add_node(node_id, node_impl)
            node_map[node_id] = node_impl

            # ConditionNode는 따로 기록 (조건부 엣지 처리용)
            if node_type == "ConditionNode":
                condition_nodes.append((node_id, node_impl, params))
        except Exception as e:
            logger.error(f"Failed to create node {node_id}: {e}")
            raise

    # 2. 일반 엣지 연결 (ConditionNode 제외 + 병렬 브랜치 제외)
    # 병렬 실행 브랜치를 찾기 위해 먼저 all_matches 모드인 ConditionNode 찾기
    fanout_sources = set()  # 병렬로 실행되는 노드들
    for node_id, node_impl, params in condition_nodes:
        if params.get("evaluation_mode") == "all_matches":
            targets = [c.get("target") for c in params.get("conditions", [])]
            fanout_sources.update(targets)

    for edge in edges:
        source = edge["source"]
        target = edge["target"]

        # source가 ConditionNode인 경우 스킵 (조건부 엣지로 처리)
        source_node = next((n for n in nodes if n["id"] == source), None)
        if source_node and source_node.get("type") == "ConditionNode":
            continue

        # 병렬 실행 브랜치 (Send로 실행되는 노드)의 엣지는 스킵
        # 이들은 Send에서 직접 처리함
        if source in fanout_sources:
            logger.debug(
                f"Skipping edge {source} -> {target} "
                f"(handled by Send/join pattern)"
            )
            continue

        # 일반 엣지 추가
        workflow.add_edge(source, target)
        logger.debug(f"Added edge: {source} -> {target}")

    # 3. ConditionNode의 조건부 엣지 추가
    for node_id, node_impl, params in condition_nodes:
        conditions = params.get("conditions", [])
        default_target = params.get("default_target", "")
        evaluation_mode = params.get("evaluation_mode", "first_match")

        # all_matches 모드인 경우, fan-out 후 join할 노드 찾기
        join_node = None
        if evaluation_mode == "all_matches":
            # 조건의 모든 타겟 노드를 찾고, 그들의 다음 노드를 확인
            condition_targets = set(c.get("target") for c in conditions)

            # 각 타겟 노드에서 나가는 엣지의 target 노드들을 찾음
            downstream_nodes = set()
            for target in condition_targets:
                for edge in edges:
                    if edge["source"] == target:
                        downstream_nodes.add(edge["target"])

            # 모든 브랜치가 공통으로 향하는 노드가 있다면, 그것이 join 노드
            if len(downstream_nodes) == 1:
                join_node = downstream_nodes.pop()
                logger.info(
                    f"ConditionNode({node_id}): "
                    f"Detected join node '{join_node}' "
                    f"for fan-out branches"
                )

        # 클로저 문제 해결을 위한 팩토리 함수
        def make_route_function(
            eval_mode: str, default: str, join: Optional[str]
        ):
            """조건부 라우팅 함수 생성 (클로저 캡처 방지)"""

            def route_condition(
                state: Dict[str, Any],
            ) -> Union[str, List[Send]]:
                """
                조건에 따라 다음 노드 결정
                - first_match: 단일 노드 ID (str) 반환
                - all_matches: Send 객체 리스트 반환 (병렬 실행)
                """
                next_value = state.get("__next__")

                # all_matches 모드: 리스트로 여러 노드에 Send
                if isinstance(next_value, list):
                    if not next_value:
                        # 빈 리스트면 default_target으로
                        return default if default else END

                    # 각 타겟 노드로 Send 객체 생성 (병렬 실행)
                    sends = []
                    for target in next_value:
                        if target:
                            # state 복사 후 브랜치 정보 추가
                            branch_state = dict(state)
                            branch_state["__branch__"] = target

                            # Send는 해당 브랜치 노드만 실행
                            # join 노드로의 이동은 add_edge로 별도 처리
                            sends.append(Send(target, branch_state))

                            logger.debug(
                                f"Creating Send to '{target}' "
                                f"(join={join})"
                            )

                    return sends if sends else (default if default else END)

                # first_match 모드: 단일 노드 ID 반환
                return next_value if next_value else default

            return route_condition

        # 가능한 모든 타겟 노드 목록 생성
        possible_targets = [c.get("target") for c in conditions]
        if default_target:
            possible_targets.append(default_target)

        # 중복 제거
        possible_targets = list(set(filter(None, possible_targets)))

        if possible_targets:
            # all_matches 모드일 때는 Send를 반환할 수 있도록 설정
            if evaluation_mode == "all_matches":
                # Send를 사용하는 경우 path_map 없이 함수만 전달
                workflow.add_conditional_edges(
                    node_id,
                    make_route_function(
                        evaluation_mode, default_target, join_node
                    ),
                )

                # 각 병렬 브랜치에서 join 노드로 가는 엣지 추가
                if join_node:
                    for target in possible_targets:
                        if (
                            target != default_target
                        ):  # default는 병렬 실행 안됨
                            workflow.add_edge(target, join_node)
                            logger.debug(
                                f"Added edge from parallel branch "
                                f"'{target}' to join '{join_node}'"
                            )

                logger.debug(
                    f"Added fan-out conditional edges from {node_id} "
                    f"(all_matches mode, join={join_node})"
                )
            else:
                # first_match 모드는 기존 방식
                workflow.add_conditional_edges(
                    node_id,
                    make_route_function(evaluation_mode, default_target, None),
                    {target: target for target in possible_targets},
                )
                logger.debug(
                    f"Added conditional edges from {node_id} "
                    f"to {possible_targets} (first_match mode)"
                )
        else:
            logger.warning(f"ConditionNode({node_id}) has no valid targets")

    # 4. 시작/끝 연결
    if nodes:
        workflow.add_edge(START, nodes[0]["id"])

        # 마지막 노드는 OutputNode일 가능성이 높음
        # 여러 경로가 있을 수 있으므로 모든 OutputNode에서 END로 연결
        for node in nodes:
            if node.get("type") == "OutputNode":
                workflow.add_edge(node["id"], END)
                logger.debug(f"Added edge: {node['id']} -> END")

        logger.debug(f"Graph flow: START -> {nodes[0]['id']}")

    # 5. 컴파일
    app = workflow.compile()
    logger.info("Graph compiled successfully")

    # 6. 실행
    logger.info(f"Executing graph with input_state: {input_state}")
    input_state["graph_status"] = "success"
    final_state = await app.ainvoke(input_state)
    logger.info("Graph execution completed")

    # 7. 구조화된 결과 생성
    structured_results = _transform_final_state_to_structured(
        final_state, nodes
    )

    return {
        "final_state": final_state,  # 기존 호환성 유지
        "structured_results": structured_results,  # 새로운 구조화된 데이터
    }


def _transform_final_state_to_structured(
    final_state: Dict[str, Any], nodes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    final_state를 구조화된 형태로 변환

    Args:
        final_state: LangGraph 실행 결과 상태
        nodes: 그래프 노드 정의 리스트

    Returns:
        구조화된 결과 데이터
    """
    results = []

    for node in nodes:
        node_id = node["id"]
        node_type = node["type"]
        node_params = node.get("params", {})
        output_key = node.get("output", "output")

        # 입력값 추출
        inputs = {}
        node_inputs = node_params.get("inputs", {})
        for input_key, input_config in node_inputs.items():
            if (
                isinstance(input_config, dict)
                and input_config.get("type") == "reference"
            ):
                ref_key = input_config["value"]
                # final_state에서 참조값 찾기
                inputs[input_key] = final_state.get(ref_key, "")
            else:
                # 직접 값인 경우
                inputs[input_key] = input_config

        # 출력값 추출
        outputs = {}
        state_key = f"{node_id}_{output_key}"
        if state_key in final_state:
            outputs[output_key] = final_state[state_key]
        else:
            # fallback: output_key로 직접 찾기
            if output_key in final_state:
                outputs[output_key] = final_state[output_key]

        # 노드별 특수 처리
        if node_type == "InputNode":
            # InputNode는 사용자 입력을 그대로 출력
            inputs["user_input"] = final_state.get(
                "input", final_state.get("user_input", "")
            )
            outputs[output_key] = inputs["user_input"]
        elif node_type == "ConditionNode":
            # ConditionNode는 조건 평가 결과 추가
            condition_result = final_state.get("__next__", "")
            outputs["condition_result"] = condition_result
            outputs["evaluated_condition"] = condition_result

        # 상태 결정 (output에 에러 메시지가 있는지 확인)
        has_error = False
        error_message = None

        # output 값들을 확인하여 에러 메시지가 있는지 체크
        for output_key, output_value in outputs.items():
            if isinstance(output_value, str) and output_value.startswith(
                "[ERROR]"
            ):
                has_error = True
                error_message = output_value.replace("[ERROR]", "").strip()
                break
        if has_error:
            status = "failed"
        elif outputs:  # output이 있으면 실행됨
            status = "success"
        else:  # output이 없으면 실행되지 않음
            status = "pending"

        results.append(
            {
                "node_id": node_id,
                "type": node_type,
                "inputs": inputs,
                "outputs": outputs,
                "status": status,
                "error_message": error_message,
            }
        )

    return {
        "results": results,
        "execution_info": {
            "total_nodes": len(nodes),
            "executed_nodes": len(
                [r for r in results if r["status"] != "pending"]
            ),
        },
    }


def _create_node(
    node_type: str,
    node_id: str,
    params: Dict[str, Any],
    output: str,
    node: Dict[str, Any],
    llm,
):
    """
    노드 타입에 따라 적절한 노드 인스턴스 생성
    """
    if node_type == "InputNode":
        return InputNode(
            output=output,
            node_id=node_id,
            **params,
        )

    elif node_type == "OutputNode":
        wrap_template = params.get("wrap_template", "")
        inputs = params.get("inputs", {})

        return OutputNode(
            output=output,
            node_id=node_id,
            wrap_template=wrap_template,
            inputs=inputs,
        )

    elif node_type == "PromptNode":
        system_prompt = params.get("system_prompt", "")
        user_prompt = params.get("user_prompt", "")
        assistant_prompt = params.get("assistant_prompt", "")
        inputs = params.get("inputs", {})

        return PromptNode(
            output=output,
            node_id=node_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            assistant_prompt=assistant_prompt,
            inputs=inputs,
            llm=llm,
        )

    elif node_type == "RetrievalNode":
        top_k = params.get("top_k", 4)
        collection = params.get("collection", "")
        inputs = params.get("inputs", {})

        return RetrievalNode(
            output=output,
            node_id=node_id,
            top_k=top_k,
            collection=collection,
            inputs=inputs,
        )

    elif node_type == "ConditionNode":
        inputs = params.get("inputs", {})
        conditions = params.get("conditions", [])
        default_target = params.get("default_target", "")
        evaluation_mode = params.get("evaluation_mode", "first_match")

        return ConditionNode(
            output=output,
            node_id=node_id,
            inputs=inputs,
            conditions=conditions,
            default_target=default_target,
            evaluation_mode=evaluation_mode,
        )

    elif node_type == "MergeNode":
        inputs = params.get("inputs", {})
        merge_strategy = params.get("merge_strategy", "concat")
        separator = params.get("separator", "\n\n---\n\n")

        return MergeNode(
            output=output,
            node_id=node_id,
            inputs=inputs,
            merge_strategy=merge_strategy,
            separator=separator,
        )

    else:
        raise ValueError(f"Unknown node type: {node_type}")
