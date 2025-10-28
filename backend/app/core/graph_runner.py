from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from app.nodes.prompt_node import PromptNode
from app.nodes.retrieval_node import RetrievalNode
from app.nodes.input_node import InputNode
from app.nodes.output_node import OutputNode
from app.nodes.condition_node import ConditionNode
import logging

logger = logging.getLogger(__name__)


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
          "id": "prompt-1",
          "type": "PromptNode",
          "params": {
            "system_prompt": "당신은 친절한 AI 어시스턴트입니다.",
            "user_prompt": "질문: {user_input}\\n참고 문서: {context}",
            "assistant_prompt": "",  # Few-shot용 (선택적)
            "inputs": {
              "user_input": {"type": "reference", "value": "user_input"},
              "context": {"type": "reference", "value": "context"}
            }
          },
          "output": "answer"
        },
        {
          "id": "output-1",
          "type": "OutputNode",
          "params": {
            "wrap_template": "답변: {answer}",
            "inputs": {
              "answer": {"type": "reference", "value": "answer"}
            }
          },
          "output": "agent_output"
        }
      ],
      "edges": [
        {"source": "input-1", "target": "retrieval-1"},
        {"source": "retrieval-1", "target": "prompt-1"},
        {"source": "prompt-1", "target": "output-1"}
      ],
      "input_state": {
        "input": "서울 날씨 어때?"
      }
    }

    하위 호환성:
    - 구버전 input_key 형식도 지원
    - template → user_prompt 자동 변환
    - variables → inputs 자동 변환
    """
    nodes = graph_json.get("nodes", [])
    edges = graph_json.get("edges", [])
    input_state = graph_json.get("input_state", {})

    # 스키마에서 이미 output 필드만 사용하도록 수정됨

    logger.info(f"Starting graph execution with {len(nodes)} nodes")

    workflow = StateGraph(dict)
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

    # 2. 일반 엣지 연결 (ConditionNode 제외)
    for edge in edges:
        source = edge["source"]
        target = edge["target"]

        # source가 ConditionNode가 아닌 경우만 일반 엣지로 연결
        source_node = next((n for n in nodes if n["id"] == source), None)
        if source_node and source_node.get("type") != "ConditionNode":
            workflow.add_edge(source, target)
            logger.debug(f"Added edge: {source} -> {target}")

    # 3. ConditionNode의 조건부 엣지 추가
    for node_id, node_impl, params in condition_nodes:
        conditions = params.get("conditions", [])
        default_target = params.get("default_target", "")

        # 조건부 라우팅 함수 생성
        def route_condition(state: Dict[str, Any]) -> str:
            """조건에 따라 다음 노드 결정"""
            return state.get("__next__", default_target)

        # 가능한 모든 타겟 노드 목록 생성
        possible_targets = [c.get("target") for c in conditions]
        if default_target:
            possible_targets.append(default_target)

        # 중복 제거
        possible_targets = list(set(filter(None, possible_targets)))

        if possible_targets:
            workflow.add_conditional_edges(
                node_id,
                route_condition,
                {target: target for target in possible_targets},
            )
            logger.debug(
                f"Added conditional edges from {node_id} "
                f"to {possible_targets}"
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
    final_state = await app.ainvoke(input_state)
    logger.info("Graph execution completed")

    return final_state


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

    하위 호환성을 위한 변환 로직 포함
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

        return ConditionNode(
            output=output,
            node_id=node_id,
            inputs=inputs,
            conditions=conditions,
            default_target=default_target,
        )

    else:
        raise ValueError(f"Unknown node type: {node_type}")
